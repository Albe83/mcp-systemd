import unittest

from mcp_systemd.backends.mock import MockSystemd
from mcp_systemd.domain.unit import UnitRef


class MockSystemdTests(unittest.IsolatedAsyncioTestCase):
    async def test_lists_system_services(self) -> None:
        backend = MockSystemd()

        units = await backend.list_units(
            unit_type="service",
            scope="system",
        )

        self.assertEqual(
            {unit.ref.name for unit in units},
            {"sshd", "systemd-journald"},
        )

    async def test_lists_user_services(self) -> None:
        backend = MockSystemd()

        units = await backend.list_units(
            unit_type="service",
            scope="user",
            user="testuser",
        )

        self.assertEqual(
            [unit.ref.name for unit in units],
            ["example-agent"],
        )

    async def test_reads_definition(self) -> None:
        backend = MockSystemd()

        definition = await backend.get_unit_definition(
            UnitRef(
                scope="system",
                type="service",
                name="sshd",
            )
        )

        self.assertIn("ExecStart=/usr/sbin/sshd -D", definition)

    async def test_rejects_unsupported_unit_type(self) -> None:
        backend = MockSystemd()

        with self.assertRaisesRegex(ValueError, "Unsupported unit type"):
            await backend.list_units(
                unit_type="mount",
                scope="system",
            )


if __name__ == "__main__":
    unittest.main()
