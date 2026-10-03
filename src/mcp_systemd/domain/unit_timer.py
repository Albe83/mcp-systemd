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
