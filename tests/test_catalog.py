import unittest

from mcp_systemd.catalog import find_unit, find_unit_by_uri


class UnitUriTests(unittest.TestCase):
    def test_resolves_canonical_system_uri(self) -> None:
        unit = find_unit_by_uri("systemd://system/unit/service/sshd")
        self.assertEqual(unit.name, "sshd")
        self.assertEqual(unit.scope, "system")

    def test_resolves_canonical_user_uri(self) -> None:
        unit = find_unit_by_uri(
            "systemd://user/testuser/unit/service/example-agent"
        )
        self.assertEqual(unit.name, "example-agent")
        self.assertEqual(unit.scope, "user")
        self.assertEqual(unit.user, "testuser")

    def test_rejects_noncanonical_base_uris(self) -> None:
        invalid_uris = (
            "systemd://system/unit/service/sshd/",
            "systemd://system/unit//service/sshd",
            "systemd://system/unit/service/sshd?view=state",
            "systemd://system/unit/service/sshd#state",
            "systemd://system/unit/service/sshd/definition",
        )

        for uri in invalid_uris:
            with self.subTest(uri=uri):
                with self.assertRaises(ValueError):
                    find_unit_by_uri(uri)

    def test_rejects_incoherent_scope_arguments(self) -> None:
        with self.assertRaises(ValueError):
            find_unit(
                scope="system",
                unit_type="service",
                name="sshd",
                user="testuser",
            )

        with self.assertRaises(ValueError):
            find_unit(
                scope="user",
                unit_type="service",
                name="example-agent",
            )


if __name__ == "__main__":
    unittest.main()
