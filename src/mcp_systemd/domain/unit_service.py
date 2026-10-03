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
