import unittest

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


class FakeSystemdManager:
    def __init__(self, rows=LIST_UNITS_ROWS) -> None:
        self.rows = rows
        self.calls = 0

    async def call_list_units(self):
        self.calls += 1
        return self.rows


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


if __name__ == "__main__":
    unittest.main()
