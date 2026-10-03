from typing import Protocol

from mcp_systemd.domain.unit import Scope, Unit, UnitRef, UnitType
from mcp_systemd.domain.unit_service import SERVICE_UNIT_TYPE
from mcp_systemd.domain.unit_timer import TIMER_UNIT_TYPE

UNIT_TYPES = (
    SERVICE_UNIT_TYPE,
    TIMER_UNIT_TYPE,
)

SUPPORTED_UNIT_TYPES = frozenset(unit_type.name for unit_type in UNIT_TYPES)


def list_unit_types() -> tuple[UnitType, ...]:
    return UNIT_TYPES


def validate_unit_query(
    *,
    unit_type: str | None = None,
    scope: Scope | None = None,
    user: str | None = None,
) -> None:
    if unit_type is not None and unit_type not in SUPPORTED_UNIT_TYPES:
        raise ValueError(f"Unsupported unit type: {unit_type}")

    if user == "":
        raise ValueError("user must be a non-empty string")

    if scope == "system" and user is not None:
        raise ValueError("system scope cannot specify a user")

    if scope == "user" and not user:
        raise ValueError("user scope requires a user")


class Systemd(Protocol):
    """Port used by the application to interact with a systemd manager."""

    async def list_units(
        self,
        *,
        unit_type: str | None = None,
        scope: Scope | None = None,
        user: str | None = None,
    ) -> tuple[Unit, ...]:
        ...

    async def get_unit(self, ref: UnitRef) -> Unit:
        ...

    async def get_unit_definition(self, ref: UnitRef) -> str:
        ...
