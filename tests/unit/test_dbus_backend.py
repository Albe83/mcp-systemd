import unittest
from unittest import mock

from dbus_fast import Variant
from dbus_fast.errors import DBusError

from mcp_systemd.backends import dbus as dbus_module
from mcp_systemd.backends.dbus import DbusSystemd
from mcp_systemd.domain.unit import UnitRef
from mcp_systemd.domain.unit_service import ServiceUnit
from mcp_systemd.domain.unit_timer import TimerUnit

LIST_UNITS_ROWS = (
    (
        "sshd.service",
        "OpenSSH server daemon",
        "loaded",
        "active",
        "running",
        "",
        "/org/freedesktop/systemd1/unit/sshd_2eservice",
        0,
        "",
        "/",
    ),
    (
        "systemd-tmpfiles-clean.timer",
        "Daily Cleanup of Temporary Directories",
        "loaded",
        "active",
        "waiting",
        "",
        "/org/freedesktop/systemd1/unit/systemd_2dtmpfiles_2dclean_2etimer",
        0,
        "",
        "/",
    ),
    (
        "dbus.socket",
        "D-Bus System Message Bus Socket",
        "loaded",
        "active",
        "running",
        "",
        "/org/freedesktop/systemd1/unit/dbus_2esocket",
        0,
        "",
        "/",
    ),
)

MALFORMED_ROWS = LIST_UNITS_ROWS + (
    (
        "trailingdot.",
        "Malformed unit name",
        "loaded",
        "active",
        "running",
        "",
        "/org/freedesktop/systemd1/unit/trailingdot",
        0,
        "",
        "/",
    ),
    (
        "nodotsuffix",
        "Malformed unit name",
        "loaded",
        "active",
        "running",
        "",
        "/org/freedesktop/systemd1/unit/nodotsuffix",
        0,
        "",
        "/",
    ),
)

ALIAS_ROWS = (
    (
        "syslog.service",
        "Syslog alias",
        "loaded",
        "active",
        "running",
        "",
        "/org/freedesktop/systemd1/unit/rsyslog_2eservice",
        0,
        "",
        "/",
    ),
    (
        "rsyslog.service",
        "System Logging Service",
        "loaded",
        "active",
        "running",
        "",
        "/org/freedesktop/systemd1/unit/rsyslog_2eservice",
        0,
        "",
        "/",
    ),
)

SYSTEMD_BUS_NAME = "org.freedesktop.systemd1"
MANAGER_PATH = "/org/freedesktop/systemd1"
MANAGER_INTERFACE = "org.freedesktop.systemd1.Manager"
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"
UNIT_INTERFACE = "org.freedesktop.systemd1.Unit"


def unit_properties(
    description: str,
    load_state: str,
    active_state: str,
    sub_state: str,
) -> dict[str, Variant]:
    return {
        "Description": Variant("s", description),
        "LoadState": Variant("s", load_state),
        "ActiveState": Variant("s", active_state),
        "SubState": Variant("s", sub_state),
    }


class FakeSystemdManager:
    def __init__(self, rows=LIST_UNITS_ROWS) -> None:
        self.rows = rows
        self.calls = 0

    async def call_list_units(self):
        self.calls += 1
        return self.rows


class FakeProxy:
    def __init__(self, manager, *, interface_error=None) -> None:
        self._manager = manager
        self._interface_error = interface_error

    def get_interface(self, name):
        if self._interface_error is not None:
            raise self._interface_error
        return self._manager


class FakeBus:
    def __init__(
        self,
        *,
        manager=None,
        proxy_error=None,
        interface_error=None,
    ) -> None:
        self._manager = manager
        self._proxy_error = proxy_error
        self._interface_error = interface_error
        self.disconnected = False

    async def connect(self):
        return self

    def get_proxy_object(self, *args, **kwargs):
        if self._proxy_error is not None:
            raise self._proxy_error
        return FakeProxy(self._manager, interface_error=self._interface_error)

    def disconnect(self):
        self.disconnected = True


class FakeManagerInterface:
    def __init__(
        self,
        *,
        rows=LIST_UNITS_ROWS,
        unit_paths=None,
        get_unit_error=None,
    ) -> None:
        self.rows = rows
        self.unit_paths = unit_paths or {}
        self.get_unit_error = get_unit_error
        self.list_calls = 0
        self.get_unit_names: list[str] = []

    async def call_list_units(self):
        self.list_calls += 1
        return self.rows

    async def call_get_unit(self, name):
        self.get_unit_names.append(name)
        if self.get_unit_error is not None:
            raise self.get_unit_error
        return self.unit_paths[name]


class FakePropertiesInterface:
    def __init__(
        self,
        properties=None,
        *,
        results=None,
        get_all_error=None,
    ) -> None:
        self._properties = properties if properties is not None else {}
        self._results = list(results) if results is not None else None
        self.get_all_error = get_all_error
        self.get_all_interfaces: list[str] = []
        self.calls = 0

    async def call_get_all(self, interface_name):
        self.get_all_interfaces.append(interface_name)
        self.calls += 1
        if self.get_all_error is not None:
            raise self.get_all_error
        if self._results is not None:
            return self._results.pop(0)
        return self._properties


class _FakeInterfaceProxy:
    def __init__(self, interface, bus, path) -> None:
        self._interface = interface
        self._bus = bus
        self._path = path

    def get_interface(self, name):
        self._bus.interface_calls.append((self._path, name))
        return self._interface


class FakeSystemBus:
    def __init__(self, *, manager, properties_by_path=None) -> None:
        self.manager = manager
        self.properties_by_path = properties_by_path or {}
        self.proxy_requests: list[tuple[str, str]] = []
        self.interface_calls: list[tuple[str, str]] = []
        self.disconnected = False

    async def connect(self):
        return self

    def get_proxy_object(self, bus_name, path, introspection):
        self.proxy_requests.append((bus_name, path))
        if path == MANAGER_PATH:
            interface = self.manager
        else:
            interface = self.properties_by_path[path]
        return _FakeInterfaceProxy(interface, self, path)

    def disconnect(self):
        self.disconnected = True


class DbusSystemdTests(unittest.IsolatedAsyncioTestCase):
    async def test_lists_supported_system_units(self) -> None:
        manager = FakeSystemdManager()
        backend = DbusSystemd(manager=manager)

        units = await backend.list_units(scope="system")

        self.assertEqual(
            [unit.ref.name for unit in units],
            ["sshd", "systemd-tmpfiles-clean"],
        )
        self.assertIsInstance(units[0], ServiceUnit)
        self.assertIsInstance(units[1], TimerUnit)
        self.assertEqual(units[0].active_state, "active")
        self.assertEqual(units[0].sub_state, "running")
        self.assertEqual(units[1].sub_state, "waiting")
        self.assertEqual(manager.calls, 1)

    async def test_filters_system_units_by_supported_type(self) -> None:
        backend = DbusSystemd(manager=FakeSystemdManager())

        units = await backend.list_units(
            unit_type="service",
            scope="system",
        )

        self.assertEqual(
            [unit.ref.name for unit in units],
            ["sshd"],
        )

    async def test_omitted_scope_lists_supported_managers(self) -> None:
        backend = DbusSystemd(manager=FakeSystemdManager())

        units = await backend.list_units()

        self.assertEqual(
            {unit.ref.scope for unit in units},
            {"system"},
        )

    async def test_rejects_user_manager_until_supported(self) -> None:
        backend = DbusSystemd(manager=FakeSystemdManager())

        with self.assertRaisesRegex(
            NotImplementedError,
            "user systemd managers",
        ):
            await backend.list_units(
                scope="user",
                user="testuser",
            )

    async def test_rejects_unsupported_unit_type(self) -> None:
        backend = DbusSystemd(manager=FakeSystemdManager())

        with self.assertRaisesRegex(ValueError, "Unsupported unit type"):
            await backend.list_units(
                unit_type="mount",
                scope="system",
            )

    async def test_rejects_user_without_scope_until_supported(self) -> None:
        backend = DbusSystemd(manager=FakeSystemdManager())

        with self.assertRaisesRegex(
            NotImplementedError,
            "user systemd managers",
        ):
            await backend.list_units(user="testuser")

    async def test_ignores_rows_without_type_suffix(self) -> None:
        backend = DbusSystemd(manager=FakeSystemdManager(MALFORMED_ROWS))

        units = await backend.list_units(scope="system")

        self.assertEqual(
            [unit.ref.name for unit in units],
            ["sshd", "systemd-tmpfiles-clean"],
        )

    async def test_preserves_aliases_sharing_object_path(self) -> None:
        backend = DbusSystemd(manager=FakeSystemdManager(ALIAS_ROWS))

        units = await backend.list_units(scope="system")

        self.assertEqual(
            [unit.ref.name for unit in units],
            ["syslog", "rsyslog"],
        )

    async def test_connects_lazily_and_reuses_bus(self) -> None:
        manager = FakeSystemdManager()
        buses: list[FakeBus] = []

        def factory(**kwargs):
            bus = FakeBus(manager=manager)
            buses.append(bus)
            return bus

        backend = DbusSystemd()
        self.assertEqual(buses, [])

        with mock.patch.object(dbus_module, "MessageBus", factory):
            first = await backend.list_units(scope="system")
            second = await backend.list_units(scope="system")

        self.assertEqual(len(buses), 1)
        self.assertEqual(manager.calls, 2)
        self.assertEqual(first, second)

    async def test_disconnects_bus_when_proxy_setup_fails(self) -> None:
        error = RuntimeError("introspection failed")
        buses: list[FakeBus] = []

        def factory(**kwargs):
            bus = FakeBus(proxy_error=error)
            buses.append(bus)
            return bus

        backend = DbusSystemd()

        with mock.patch.object(dbus_module, "MessageBus", factory):
            with self.assertRaises(RuntimeError) as raised:
                await backend.list_units(scope="system")

        self.assertIs(raised.exception, error)
        self.assertTrue(buses[0].disconnected)
        self.assertIsNone(backend._bus)
        self.assertIsNone(backend._manager)

    async def test_disconnects_bus_when_interface_setup_fails(self) -> None:
        error = RuntimeError("interface missing")
        buses: list[FakeBus] = []

        def factory(**kwargs):
            bus = FakeBus(interface_error=error)
            buses.append(bus)
            return bus

        backend = DbusSystemd()

        with mock.patch.object(dbus_module, "MessageBus", factory):
            with self.assertRaises(RuntimeError) as raised:
                await backend.list_units(scope="system")

        self.assertIs(raised.exception, error)
        self.assertTrue(buses[0].disconnected)
        self.assertIsNone(backend._bus)
        self.assertIsNone(backend._manager)

    async def test_reads_current_service_state(self) -> None:
        service_path = "/org/freedesktop/systemd1/unit/sshd_2eservice"
        manager = FakeManagerInterface(unit_paths={"sshd.service": service_path})
        properties = FakePropertiesInterface(
            unit_properties("OpenSSH server daemon", "loaded", "active", "running")
        )
        bus = FakeSystemBus(
            manager=manager,
            properties_by_path={service_path: properties},
        )
        backend = DbusSystemd()
        ref = UnitRef(scope="system", type="service", name="sshd")

        with mock.patch.object(dbus_module, "MessageBus", lambda **kwargs: bus):
            unit = await backend.get_unit(ref)

        self.assertIsInstance(unit, ServiceUnit)
        self.assertEqual(unit.ref, ref)
        self.assertEqual(unit.description, "OpenSSH server daemon")
        self.assertEqual(unit.load_state, "loaded")
        self.assertEqual(unit.active_state, "active")
        self.assertEqual(unit.sub_state, "running")
        self.assertEqual(manager.get_unit_names, ["sshd.service"])
        self.assertEqual(properties.get_all_interfaces, [UNIT_INTERFACE])

    async def test_reads_current_timer_state(self) -> None:
        timer_path = "/org/freedesktop/systemd1/unit/clean_2etimer"
        manager = FakeManagerInterface(unit_paths={"clean.timer": timer_path})
        properties = FakePropertiesInterface(
            unit_properties("Cleanup", "loaded", "active", "waiting")
        )
        bus = FakeSystemBus(
            manager=manager,
            properties_by_path={timer_path: properties},
        )
        backend = DbusSystemd()
        ref = UnitRef(scope="system", type="timer", name="clean")

        with mock.patch.object(dbus_module, "MessageBus", lambda **kwargs: bus):
            unit = await backend.get_unit(ref)

        self.assertIsInstance(unit, TimerUnit)
        self.assertEqual(unit.ref, ref)
        self.assertEqual(unit.sub_state, "waiting")
        self.assertEqual(manager.get_unit_names, ["clean.timer"])

    async def test_sends_exact_unit_name_and_object_arguments(self) -> None:
        unit_path = "/org/freedesktop/systemd1/unit/foo_2ebar_40instance_2eservice"
        manager = FakeManagerInterface(
            unit_paths={"foo.bar@instance.service": unit_path}
        )
        properties = FakePropertiesInterface(
            unit_properties("Instance", "loaded", "inactive", "dead")
        )
        bus = FakeSystemBus(
            manager=manager,
            properties_by_path={unit_path: properties},
        )
        backend = DbusSystemd()
        ref = UnitRef(scope="system", type="service", name="foo.bar@instance")

        with mock.patch.object(dbus_module, "MessageBus", lambda **kwargs: bus):
            await backend.get_unit(ref)

        self.assertEqual(manager.get_unit_names, ["foo.bar@instance.service"])
        self.assertIn((SYSTEMD_BUS_NAME, MANAGER_PATH), bus.proxy_requests)
        self.assertIn((MANAGER_PATH, MANAGER_INTERFACE), bus.interface_calls)
        self.assertIn((SYSTEMD_BUS_NAME, unit_path), bus.proxy_requests)
        self.assertIn((unit_path, PROPERTIES_INTERFACE), bus.interface_calls)

    async def test_alias_resolution_keeps_requested_ref(self) -> None:
        primary_path = "/org/freedesktop/systemd1/unit/rsyslog_2eservice"
        manager = FakeManagerInterface(
            unit_paths={"syslog.service": primary_path}
        )
        properties = FakePropertiesInterface(
            unit_properties("System Logging Service", "loaded", "active", "running")
        )
        bus = FakeSystemBus(
            manager=manager,
            properties_by_path={primary_path: properties},
        )
        backend = DbusSystemd()
        ref = UnitRef(scope="system", type="service", name="syslog")

        with mock.patch.object(dbus_module, "MessageBus", lambda **kwargs: bus):
            unit = await backend.get_unit(ref)

        self.assertEqual(unit.ref, ref)
        self.assertEqual(unit.ref.name, "syslog")
        self.assertEqual(properties.get_all_interfaces, [UNIT_INTERFACE])

    async def test_two_reads_return_changed_state_without_list(self) -> None:
        unit_path = "/org/freedesktop/systemd1/unit/sshd_2eservice"
        manager = FakeManagerInterface(unit_paths={"sshd.service": unit_path})
        properties = FakePropertiesInterface(
            results=(
                unit_properties("OpenSSH", "loaded", "active", "running"),
                unit_properties("OpenSSH", "loaded", "inactive", "dead"),
            )
        )
        bus = FakeSystemBus(
            manager=manager,
            properties_by_path={unit_path: properties},
        )
        backend = DbusSystemd()
        ref = UnitRef(scope="system", type="service", name="sshd")

        with mock.patch.object(dbus_module, "MessageBus", lambda **kwargs: bus):
            first = await backend.get_unit(ref)
            second = await backend.get_unit(ref)

        self.assertEqual(first.active_state, "active")
        self.assertEqual(first.sub_state, "running")
        self.assertEqual(second.active_state, "inactive")
        self.assertEqual(second.sub_state, "dead")
        self.assertEqual(manager.get_unit_names, ["sshd.service", "sshd.service"])
        self.assertEqual(manager.list_calls, 0)
        self.assertEqual(properties.calls, 2)

    async def test_rejects_user_reference_before_bus_use(self) -> None:
        created: list[dict] = []
        backend = DbusSystemd()
        ref = UnitRef(scope="user", type="service", name="agent", user="alice")

        with mock.patch.object(
            dbus_module,
            "MessageBus",
            lambda **kwargs: created.append(kwargs),
        ):
            with self.assertRaisesRegex(
                NotImplementedError,
                "user systemd managers",
            ):
                await backend.get_unit(ref)

        self.assertEqual(created, [])

    async def test_rejects_unsupported_type_before_bus_use(self) -> None:
        created: list[dict] = []
        backend = DbusSystemd()
        ref = UnitRef(scope="system", type="mount", name="boot")

        with mock.patch.object(
            dbus_module,
            "MessageBus",
            lambda **kwargs: created.append(kwargs),
        ):
            with self.assertRaisesRegex(ValueError, "Unsupported unit type"):
                await backend.get_unit(ref)

        self.assertEqual(created, [])

    async def test_no_such_unit_becomes_value_error(self) -> None:
        error = DBusError("org.freedesktop.systemd1.NoSuchUnit", "Unit not found")
        manager = FakeManagerInterface(get_unit_error=error)
        bus = FakeSystemBus(manager=manager)
        backend = DbusSystemd()
        ref = UnitRef(scope="system", type="service", name="ghost")

        with mock.patch.object(dbus_module, "MessageBus", lambda **kwargs: bus):
            with self.assertRaisesRegex(ValueError, "Unit not found") as raised:
                await backend.get_unit(ref)

        self.assertIs(raised.exception.__cause__, error)
        self.assertFalse(bus.disconnected)

    async def test_unknown_object_during_property_read_becomes_value_error(
        self,
    ) -> None:
        unit_path = "/org/freedesktop/systemd1/unit/sshd_2eservice"
        error = DBusError("org.freedesktop.DBus.Error.UnknownObject", "gone")
        manager = FakeManagerInterface(unit_paths={"sshd.service": unit_path})
        properties = FakePropertiesInterface(get_all_error=error)
        bus = FakeSystemBus(
            manager=manager,
            properties_by_path={unit_path: properties},
        )
        backend = DbusSystemd()
        ref = UnitRef(scope="system", type="service", name="sshd")

        with mock.patch.object(dbus_module, "MessageBus", lambda **kwargs: bus):
            with self.assertRaisesRegex(ValueError, "Unit not found") as raised:
                await backend.get_unit(ref)

        self.assertIs(raised.exception.__cause__, error)
        self.assertFalse(bus.disconnected)

    async def test_access_denied_propagates_unchanged(self) -> None:
        error = DBusError("org.freedesktop.DBus.Error.AccessDenied", "denied")
        manager = FakeManagerInterface(get_unit_error=error)
        bus = FakeSystemBus(manager=manager)
        backend = DbusSystemd()
        ref = UnitRef(scope="system", type="service", name="sshd")

        with mock.patch.object(dbus_module, "MessageBus", lambda **kwargs: bus):
            with self.assertRaises(DBusError) as raised:
                await backend.get_unit(ref)

        self.assertIs(raised.exception, error)

    async def test_unrelated_dbus_error_during_property_read_propagates(
        self,
    ) -> None:
        unit_path = "/org/freedesktop/systemd1/unit/sshd_2eservice"
        error = DBusError("org.freedesktop.DBus.Error.Failed", "boom")
        manager = FakeManagerInterface(unit_paths={"sshd.service": unit_path})
        properties = FakePropertiesInterface(get_all_error=error)
        bus = FakeSystemBus(
            manager=manager,
            properties_by_path={unit_path: properties},
        )
        backend = DbusSystemd()
        ref = UnitRef(scope="system", type="service", name="sshd")

        with mock.patch.object(dbus_module, "MessageBus", lambda **kwargs: bus):
            with self.assertRaises(DBusError) as raised:
                await backend.get_unit(ref)

        self.assertIs(raised.exception, error)

    async def test_missing_required_property_fails_explicitly(self) -> None:
        unit_path = "/org/freedesktop/systemd1/unit/sshd_2eservice"
        manager = FakeManagerInterface(unit_paths={"sshd.service": unit_path})
        properties = unit_properties("OpenSSH", "loaded", "active", "running")
        del properties["SubState"]
        bus = FakeSystemBus(
            manager=manager,
            properties_by_path={unit_path: FakePropertiesInterface(properties)},
        )
        backend = DbusSystemd()
        ref = UnitRef(scope="system", type="service", name="sshd")

        with mock.patch.object(dbus_module, "MessageBus", lambda **kwargs: bus):
            with self.assertRaisesRegex(ValueError, "SubState"):
                await backend.get_unit(ref)

    async def test_malformed_required_property_fails_explicitly(self) -> None:
        unit_path = "/org/freedesktop/systemd1/unit/sshd_2eservice"
        manager = FakeManagerInterface(unit_paths={"sshd.service": unit_path})
        properties = unit_properties("OpenSSH", "loaded", "active", "running")
        properties["Description"] = "not-a-variant"
        bus = FakeSystemBus(
            manager=manager,
            properties_by_path={unit_path: FakePropertiesInterface(properties)},
        )
        backend = DbusSystemd()
        ref = UnitRef(scope="system", type="service", name="sshd")

        with mock.patch.object(dbus_module, "MessageBus", lambda **kwargs: bus):
            with self.assertRaisesRegex(ValueError, "Description"):
                await backend.get_unit(ref)

    async def test_get_unit_reuses_bus_created_by_list_units(self) -> None:
        unit_path = "/org/freedesktop/systemd1/unit/sshd_2eservice"
        manager = FakeManagerInterface(unit_paths={"sshd.service": unit_path})
        properties = FakePropertiesInterface(
            unit_properties("OpenSSH", "loaded", "active", "running")
        )
        bus = FakeSystemBus(
            manager=manager,
            properties_by_path={unit_path: properties},
        )
        created: list[dict] = []

        def factory(**kwargs):
            created.append(kwargs)
            return bus

        backend = DbusSystemd()

        with mock.patch.object(dbus_module, "MessageBus", factory):
            await backend.list_units(scope="system")
            unit = await backend.get_unit(
                UnitRef(scope="system", type="service", name="sshd")
            )

        self.assertEqual(len(created), 1)
        self.assertEqual(manager.list_calls, 1)
        self.assertEqual(unit.sub_state, "running")


if __name__ == "__main__":
    unittest.main()
