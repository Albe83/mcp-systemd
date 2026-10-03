import unittest
from unittest import mock

from mcp_systemd.backends import dbus as dbus_module
from mcp_systemd.backends.dbus import DbusSystemd
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


class FakeSystemdManager:
    def __init__(self, rows=LIST_UNITS_ROWS) -> None:
        self.rows = rows
        self.calls = 0

    async def call_list_units(self):
        self.calls += 1
        return self.rows


class FakeProxy:
    def __init__(self, manager) -> None:
        self._manager = manager

    def get_interface(self, name):
        return self._manager


class FakeBus:
    def __init__(self, *, manager=None, proxy_error=None) -> None:
        self._manager = manager
        self._proxy_error = proxy_error
        self.disconnected = False

    async def connect(self):
        return self

    def get_proxy_object(self, *args, **kwargs):
        if self._proxy_error is not None:
            raise self._proxy_error
        return FakeProxy(self._manager)

    async def disconnect(self):
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

    async def test_disconnects_bus_when_manager_setup_fails(self) -> None:
        buses: list[FakeBus] = []

        def factory(**kwargs):
            bus = FakeBus(proxy_error=RuntimeError("introspection failed"))
            buses.append(bus)
            return bus

        backend = DbusSystemd()

        with mock.patch.object(dbus_module, "MessageBus", factory):
            with self.assertRaises(RuntimeError):
                await backend.list_units(scope="system")

        self.assertTrue(buses[0].disconnected)
        self.assertIsNone(backend._bus)
        self.assertIsNone(backend._manager)


if __name__ == "__main__":
    unittest.main()
