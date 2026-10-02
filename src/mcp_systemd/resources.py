from dataclasses import dataclass
from typing import Literal

from fastmcp.resources import Resource
from fastmcp.server.providers import Provider

Scope = Literal["system", "user"]


@dataclass(frozen=True)
class UnitTypeRecord:
    name: str
    description: str


UNIT_TYPES = (
    UnitTypeRecord(
        name="service",
        description=(
            "A unit that represents and controls a service or process managed by systemd."
        ),
    ),
    UnitTypeRecord(
        name="timer",
        description=(
            "A unit that schedules time-based activation of another systemd unit."
        ),
    ),
)

SUPPORTED_TYPES = {unit_type.name for unit_type in UNIT_TYPES}


@dataclass(frozen=True)
class UnitRecord:
    scope: Scope
    type: str
    name: str
    description: str
    user: str | None = None

    @property
    def uri(self) -> str:
        if self.scope == "system":
            return f"systemd://system/unit/{self.type}/{self.name}"

        if self.user is None:
            raise ValueError("user-scoped units require a user")

        return f"systemd://user/{self.user}/unit/{self.type}/{self.name}"

    def content(self) -> dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
        }

    def discovery(self) -> dict[str, str]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
        }


MOCK_UNITS = (
    UnitRecord(
        scope="system",
        type="service",
        name="sshd",
        description="OpenSSH server daemon",
    ),
    UnitRecord(
        scope="system",
        type="service",
        name="systemd-journald",
        description="Journal Service",
    ),
    UnitRecord(
        scope="system",
        type="timer",
        name="systemd-tmpfiles-clean",
        description="Daily Cleanup of Temporary Directories",
    ),
    UnitRecord(
        scope="user",
        user="testuser",
        type="service",
        name="example-agent",
        description="Example user service",
    ),
)


def list_unit_records() -> tuple[UnitRecord, ...]:
    """Return the unit catalog exposed by resources/list and list_units."""
    return MOCK_UNITS


def list_unit_type_records() -> tuple[UnitTypeRecord, ...]:
    return UNIT_TYPES


def find_unit(
    *,
    scope: Scope,
    unit_type: str,
    name: str,
    user: str | None = None,
) -> UnitRecord:
    if unit_type not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported unit type: {unit_type}")

    for unit in MOCK_UNITS:
        if (
            unit.scope == scope
            and unit.type == unit_type
            and unit.name == name
            and unit.user == user
        ):
            return unit

    raise ValueError("Unit not found")


def _resource_from_unit(unit: UnitRecord) -> Resource:
    def read_unit() -> dict[str, str]:
        return unit.content()

    return Resource.from_function(
        fn=read_unit,
        uri=unit.uri,
        name=unit.name,
        description=unit.description,
        mime_type="application/json",
    )


class MockUnitProvider(Provider):
    """Expose the mock unit catalog as concrete MCP resources."""

    async def _list_resources(self) -> list[Resource]:
        return [_resource_from_unit(unit) for unit in list_unit_records()]
