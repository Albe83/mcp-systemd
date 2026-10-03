from fastmcp import FastMCP
from fastmcp.resources import Resource
from fastmcp.server.providers import Provider

from mcp_systemd.domain.systemd import Systemd
from mcp_systemd.domain.unit import Unit, UnitRef
from mcp_systemd.mcp_unit import unit_content, unit_uri

SYSTEM_UNIT_DESCRIPTION = "A systemd unit managed by the system service manager."
USER_UNIT_DESCRIPTION = "A systemd unit managed by a user's service manager."
UNIT_DEFINITION_DESCRIPTION = "Unit file and drop-ins for a systemd unit."


def _resource_from_unit(unit: Unit, systemd: Systemd) -> Resource:
    ref = unit.ref

    async def read_unit() -> dict[str, str]:
        current = await systemd.get_unit(ref)
        return unit_content(current)

    return Resource.from_function(
        fn=read_unit,
        uri=unit_uri(ref),
        name=ref.name,
        description=unit.description,
        mime_type="application/json",
    )


class UnitResourceProvider(Provider):
    """Expose domain units as concrete MCP resources."""

    def __init__(self, systemd: Systemd) -> None:
        super().__init__()
        self._systemd = systemd

    async def _list_resources(self) -> list[Resource]:
        units = await self._systemd.list_units()
        return [
            _resource_from_unit(unit, self._systemd)
            for unit in units
        ]


def register_resources(mcp: FastMCP, systemd: Systemd) -> None:
    mcp.add_provider(UnitResourceProvider(systemd))

    @mcp.resource(
        "systemd://system/unit/{type}/{name}",
        name="System unit",
        description=SYSTEM_UNIT_DESCRIPTION,
        mime_type="application/json",
    )
    async def system_unit(type: str, name: str) -> dict[str, str]:
        unit = await systemd.get_unit(
            UnitRef(
                scope="system",
                type=type,
                name=name,
            )
        )
        return unit_content(unit)

    @mcp.resource(
        "systemd://user/{user}/unit/{type}/{name}",
        name="User unit",
        description=USER_UNIT_DESCRIPTION,
        mime_type="application/json",
    )
    async def user_unit(
        user: str,
        type: str,
        name: str,
    ) -> dict[str, str]:
        unit = await systemd.get_unit(
            UnitRef(
                scope="user",
                user=user,
                type=type,
                name=name,
            )
        )
        return unit_content(unit)

    @mcp.resource(
        "systemd://system/unit/{type}/{name}/definition",
        name="Unit definition",
        description=UNIT_DEFINITION_DESCRIPTION,
        mime_type="text/plain",
    )
    async def system_unit_definition(type: str, name: str) -> str:
        return await systemd.get_unit_definition(
            UnitRef(
                scope="system",
                type=type,
                name=name,
            )
        )

    @mcp.resource(
        "systemd://user/{user}/unit/{type}/{name}/definition",
        name="Unit definition",
        description=UNIT_DEFINITION_DESCRIPTION,
        mime_type="text/plain",
    )
    async def user_unit_definition(
        user: str,
        type: str,
        name: str,
    ) -> str:
        return await systemd.get_unit_definition(
            UnitRef(
                scope="user",
                user=user,
                type=type,
                name=name,
            )
        )
