import unittest

from mcp_systemd.domain.unit import UnitRef
from mcp_systemd.domain.unit_service import ServiceUnit
from mcp_systemd.domain.unit_timer import TimerUnit


class UnitModelTests(unittest.TestCase):
    def test_user_scope_requires_user(self) -> None:
        with self.assertRaisesRegex(ValueError, "user scope requires a user"):
            UnitRef(
                scope="user",
                type="service",
                name="example",
            )

    def test_service_unit_requires_service_ref(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "ServiceUnit requires a service UnitRef",
        ):
            ServiceUnit(
                ref=UnitRef(
                    scope="system",
                    type="timer",
                    name="example",
                ),
                description="Example",
                load_state="loaded",
                active_state="active",
                sub_state="waiting",
            )

    def test_timer_unit_requires_timer_ref(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "TimerUnit requires a timer UnitRef",
        ):
            TimerUnit(
                ref=UnitRef(
                    scope="system",
                    type="service",
                    name="example",
                ),
                description="Example",
                load_state="loaded",
                active_state="active",
                sub_state="running",
            )


if __name__ == "__main__":
    unittest.main()
