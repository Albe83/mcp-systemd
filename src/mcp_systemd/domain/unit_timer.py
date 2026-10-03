from dataclasses import dataclass

from mcp_systemd.domain.unit import Unit, UnitType

TIMER_UNIT_TYPE = UnitType(
    name="timer",
    description=(
        "A unit that schedules time-based activation of another systemd unit."
    ),
)


@dataclass(frozen=True)
class TimerUnit(Unit):
    """A systemd timer unit."""

    def __post_init__(self) -> None:
        if self.ref.type != TIMER_UNIT_TYPE.name:
            raise ValueError("TimerUnit requires a timer UnitRef")
