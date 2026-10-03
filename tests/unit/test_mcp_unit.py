import unittest

from mcp_systemd.domain.unit import Unit, UnitRef
from mcp_systemd.mcp_unit import (
    parse_unit_uri,
    unit_content,
    unit_discovery,
    unit_uri,
)


class UnitUriTests(unittest.TestCase):
    def test_round_trip_system_unit(self) -> None:
        ref = UnitRef(
            scope="system",
            type="service",
            name="sshd",
        )
        uri = unit_uri(ref)

        self.assertEqual(uri, "systemd://system/unit/service/sshd")
        self.assertEqual(parse_unit_uri(uri), ref)

    def test_round_trip_user_unit(self) -> None:
        ref = UnitRef(
            scope="user",
            user="testuser",
            type="service",
            name="example-agent",
        )
        uri = unit_uri(ref)

        self.assertEqual(
            uri,
            "systemd://user/testuser/unit/service/example-agent",
        )
        self.assertEqual(parse_unit_uri(uri), ref)

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
                    parse_unit_uri(uri)

    def test_mcp_serialization_is_outside_domain_model(self) -> None:
        unit = Unit(
            ref=UnitRef(
                scope="system",
                type="service",
                name="sshd",
            ),
            description="OpenSSH server daemon",
            load_state="loaded",
            active_state="active",
            sub_state="running",
        )

        self.assertEqual(
            unit_content(unit),
            {
                "description": "OpenSSH server daemon",
                "load_state": "loaded",
                "active_state": "active",
                "sub_state": "running",
            },
        )
        self.assertEqual(
            unit_discovery(unit),
            {
                "uri": "systemd://system/unit/service/sshd",
                "name": "sshd",
                "description": "OpenSSH server daemon",
            },
        )


if __name__ == "__main__":
    unittest.main()
