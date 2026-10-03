import contextlib
import io
import json
import unittest
from unittest import mock

from dbus_fast import Variant
from dbus_fast.errors import DBusError

from scripts import inspect_unit_properties as inspect_module
from scripts.inspect_unit_properties import (
    PROPERTIES_INTERFACE,
    SYSTEMD_BUS_NAME,
    SYSTEMD_MANAGER_INTERFACE,
    SYSTEMD_MANAGER_PATH,
    inspect_unit_properties,
    main,
    validate_unit_name,
)

MANAGER_INTERFACE_NAME = "org.freedesktop.systemd1.Manager"


class ValidateUnitNameTests(unittest.TestCase):
    def test_accepts_service_and_timer_names_verbatim(self) -> None:
        for name in (
            "sshd.service",
            "logrotate.timer",
            "foo.bar@instance.service",
            "a.b.c.timer",
        ):
            with self.subTest(name=name):
                self.assertEqual(validate_unit_name(name), name)

    def test_rejects_invalid_names(self) -> None:
        for name in ("sshd", "foo.mount", "foo.socket", ".service", "foo."):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validate_unit_name(name)


class SerializeTests(unittest.TestCase):
    def test_serializes_scalars_and_preserves_signature(self) -> None:
        self.assertEqual(
            inspect_module._serialize(Variant("s", "")),
            {"signature": "s", "value": ""},
        )
        self.assertEqual(
            inspect_module._serialize(Variant("b", False)),
            {"signature": "b", "value": False},
        )
        self.assertEqual(
            inspect_module._serialize(Variant("t", 0)),
            {"signature": "t", "value": 0},
        )

    def test_serializes_arrays_structs_and_bytes(self) -> None:
        self.assertEqual(
            inspect_module._serialize(Variant("as", [])),
            {"signature": "as", "value": []},
        )
        self.assertEqual(
            inspect_module._serialize(Variant("ay", b"\x00\x01")),
            {"signature": "ay", "value": [0, 1]},
        )
        self.assertEqual(
            inspect_module._serialize(Variant("(ss)", ("a", "b"))),
            {"signature": "(ss)", "value": ["a", "b"]},
        )

    def test_serializes_nested_variant_and_dictionaries(self) -> None:
        self.assertEqual(
            inspect_module._serialize(Variant("v", Variant("s", "x"))),
            {
                "signature": "v",
                "value": {"signature": "s", "value": "x"},
            },
        )
        self.assertEqual(
            inspect_module._serialize({"B": 1, "A": 2}),
            {"B": 1, "A": 2},
        )

    def test_rejects_unsupported_values(self) -> None:
        with self.assertRaises(TypeError):
            inspect_module._serialize(object())


class FakeIntrospectionInterface:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeNode:
    def __init__(self, interface_names) -> None:
        self.interfaces = [
            FakeIntrospectionInterface(name)
            for name in interface_names
        ]


class FakeManagerInterface:
    def __init__(self, object_path, *, error=None) -> None:
        self.object_path = object_path
        self.error = error
        self.get_unit_names: list[str] = []

    async def call_get_unit(self, name):
        self.get_unit_names.append(name)
        if self.error is not None:
            raise self.error
        return self.object_path


class FakePropertiesInterface:
    def __init__(self, properties_by_interface, *, error=None) -> None:
        self.properties_by_interface = properties_by_interface
        self.error = error
        self.get_all_names: list[str] = []

    async def call_get_all(self, interface_name):
        self.get_all_names.append(interface_name)
        if self.error is not None:
            raise self.error
        return self.properties_by_interface[interface_name]


class FakeProxy:
    def __init__(self, interface, bus, path) -> None:
        self._interface = interface
        self._bus = bus
        self._path = path

    def get_interface(self, name):
        self._bus.interface_requests.append((self._path, name))
        return self._interface


class FakeBus:
    def __init__(
        self,
        *,
        manager,
        unit_path="/unused",
        unit_interfaces=(),
        properties=None,
        introspect_error=None,
    ) -> None:
        self.manager = manager
        self.unit_path = unit_path
        self.unit_interfaces = unit_interfaces
        self.properties = properties
        self.introspect_error = introspect_error
        self.proxy_requests: list[tuple[str, str]] = []
        self.interface_requests: list[tuple[str, str]] = []
        self.introspect_requests: list[tuple[str, str]] = []
        self.disconnected = False

    async def connect(self):
        return self

    def get_proxy_object(self, bus_name, path, introspection):
        self.proxy_requests.append((bus_name, path))
        interface = self.manager if path == SYSTEMD_MANAGER_PATH else self.properties
        return FakeProxy(interface, self, path)

    async def introspect(self, bus_name, path):
        if self.introspect_error is not None:
            raise self.introspect_error
        self.introspect_requests.append((bus_name, path))
        return FakeNode(self.unit_interfaces)

    def disconnect(self):
        self.disconnected = True


def _patch_bus(bus):
    return mock.patch.object(inspect_module, "MessageBus", lambda **kwargs: bus)


def _unit_properties():
    return {
        "org.freedesktop.systemd1.Unit": {
            "Description": Variant("s", "Example"),
            "ActiveState": Variant("s", "active"),
        },
        "org.freedesktop.systemd1.Service": {
            "ExecStart": Variant("a(sasbttttuii)", []),
            "Restart": Variant("s", "on-failure"),
            "Type": Variant("s", "simple"),
        },
    }


UNIT_INTERFACES = (
    "org.freedesktop.DBus.Peer",
    "org.freedesktop.DBus.Properties",
    "org.freedesktop.systemd1.Service",
    "org.freedesktop.systemd1.Unit",
)


class InspectUnitPropertiesTests(unittest.IsolatedAsyncioTestCase):
    async def test_resolves_exact_name_and_reads_native_interfaces(self) -> None:
        manager = FakeManagerInterface("/org/freedesktop/systemd1/unit/x_2eservice")
        properties = FakePropertiesInterface(_unit_properties())
        bus = FakeBus(
            manager=manager,
            unit_path="/org/freedesktop/systemd1/unit/x_2eservice",
            unit_interfaces=UNIT_INTERFACES,
            properties=properties,
        )

        with _patch_bus(bus):
            result = await inspect_unit_properties("foo.bar@instance.service")

        self.assertEqual(result["requested_unit"], "foo.bar@instance.service")
        self.assertEqual(
            result["object_path"],
            "/org/freedesktop/systemd1/unit/x_2eservice",
        )
        self.assertEqual(
            list(result["interfaces"]),
            [
                "org.freedesktop.systemd1.Service",
                "org.freedesktop.systemd1.Unit",
            ],
        )
        self.assertEqual(
            list(result["interfaces"]["org.freedesktop.systemd1.Service"]),
            ["ExecStart", "Restart", "Type"],
        )
        self.assertEqual(
            manager.get_unit_names,
            ["foo.bar@instance.service"],
        )
        self.assertEqual(
            properties.get_all_names,
            [
                "org.freedesktop.systemd1.Service",
                "org.freedesktop.systemd1.Unit",
            ],
        )
        self.assertIn((SYSTEMD_BUS_NAME, SYSTEMD_MANAGER_PATH), bus.proxy_requests)
        self.assertIn(
            (SYSTEMD_MANAGER_PATH, SYSTEMD_MANAGER_INTERFACE),
            bus.interface_requests,
        )
        self.assertIn(
            (
                "/org/freedesktop/systemd1/unit/x_2eservice",
                PROPERTIES_INTERFACE,
            ),
            bus.interface_requests,
        )
        self.assertEqual(
            bus.introspect_requests,
            [
                (
                    SYSTEMD_BUS_NAME,
                    "/org/freedesktop/systemd1/unit/x_2eservice",
                )
            ],
        )
        self.assertTrue(bus.disconnected)

    async def test_rejects_invalid_name_before_connecting(self) -> None:
        created: list[dict] = []

        def factory(**kwargs):
            created.append(kwargs)

        with mock.patch.object(inspect_module, "MessageBus", factory):
            with self.assertRaises(ValueError):
                await inspect_unit_properties("foo.mount")

        self.assertEqual(created, [])

    async def test_read_failure_disconnects_bus(self) -> None:
        error = RuntimeError("read failed")
        manager = FakeManagerInterface("/org/freedesktop/systemd1/unit/x_2eservice")
        properties = FakePropertiesInterface({}, error=error)
        bus = FakeBus(
            manager=manager,
            unit_path="/org/freedesktop/systemd1/unit/x_2eservice",
            unit_interfaces=UNIT_INTERFACES,
            properties=properties,
        )

        with _patch_bus(bus):
            with self.assertRaises(RuntimeError) as raised:
                await inspect_unit_properties("sshd.service")

        self.assertIs(raised.exception, error)
        self.assertTrue(bus.disconnected)

    async def test_unknown_unit_propagates_without_fallback(self) -> None:
        error = DBusError(
            "org.freedesktop.systemd1.NoSuchUnit",
            "Unit not found",
        )
        manager = FakeManagerInterface("/unused", error=error)
        bus = FakeBus(manager=manager)

        with _patch_bus(bus):
            with self.assertRaises(DBusError) as raised:
                await inspect_unit_properties("ghost.service")

        self.assertIs(raised.exception, error)
        self.assertEqual(manager.get_unit_names, ["ghost.service"])
        self.assertTrue(bus.disconnected)


class MainTests(unittest.TestCase):
    def test_prints_single_json_document_to_stdout(self) -> None:
        result = {
            "requested_unit": "x.service",
            "object_path": "/org/freedesktop/systemd1/unit/x_2eservice",
            "interfaces": {},
        }

        async def fake(name):
            return result

        stdout = io.StringIO()
        with mock.patch.object(
            inspect_module,
            "inspect_unit_properties",
            new=fake,
        ):
            with contextlib.redirect_stdout(stdout):
                code = main(["x.service"])

        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue()), result)

    def test_rejects_unsupported_unit_suffix(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(["foo.mount"])

        self.assertNotEqual(code, 0)
        self.assertIn("foo.mount", stderr.getvalue())

    def test_failure_prints_no_json(self) -> None:
        async def fake(name):
            raise RuntimeError("boom")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(
            inspect_module,
            "inspect_unit_properties",
            new=fake,
        ):
            with contextlib.redirect_stdout(stdout):
                with contextlib.redirect_stderr(stderr):
                    code = main(["x.service"])

        self.assertNotEqual(code, 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("boom", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
