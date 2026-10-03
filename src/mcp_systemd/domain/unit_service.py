from dataclasses import dataclass

from mcp_systemd.domain.unit import Unit, UnitType

SERVICE_UNIT_TYPE = UnitType(
    name="service",
    description=(
        "A unit that represents and controls a service or process managed by systemd."
    ),
)


@dataclass(frozen=True)
class ServiceUnit(Unit):
    """A systemd service unit."""

    def __post_init__(self) -> None:
        if self.ref.type != SERVICE_UNIT_TYPE.name:
            raise ValueError("ServiceUnit requires a service UnitRef")
