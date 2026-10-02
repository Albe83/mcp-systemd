from fastmcp import FastMCP
from fastmcp.resources import Resource
from fastmcp.server.providers import Provider

from mcp_systemd.catalog import UnitRecord, find_unit, list_unit_records

SYSTEM_UNIT_DESCRIPTION = "A systemd unit managed by the system service manager."
USER_UNIT_DESCRIPTION = "A systemd unit managed by a user's service manager."
UNIT_DEFINITION_DESCRIPTION = "Unit file and drop-ins for a systemd unit."


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


def register_resources(mcp: FastMCP) -> None:
    mcp.add_provider(MockUnitProvider())

    @mcp.resource(
        "systemd://system/unit/{type}/{name}",
        name="System unit",
        description=SYSTEM_UNIT_DESCRIPTION,
        mime_type="application/json",
    )
    def system_unit(type: str, name: str) -> dict[str, str]:
        return find_unit(
            scope="system",
            unit_type=type,
            name=name,
        ).content()

    @mcp.resource(
        "systemd://user/{user}/unit/{type}/{name}",
        name="User unit",
        description=USER_UNIT_DESCRIPTION,
        mime_type="application/json",
    )
    def user_unit(user: str, type: str, name: str) -> dict[str, str]:
        return find_unit(
            scope="user",
            user=user,
            unit_type=type,
            name=name,
        ).content()

    @mcp.resource(
        "systemd://system/unit/{type}/{name}/definition",
        name="Unit definition",
        description=UNIT_DEFINITION_DESCRIPTION,
        mime_type="text/plain",
    )
    def system_unit_definition(type: str, name: str) -> str:
        return find_unit(
            scope="system",
            unit_type=type,
            name=name,
        ).definition

    @mcp.resource(
        "systemd://user/{user}/unit/{type}/{name}/definition",
        name="Unit definition",
        description=UNIT_DEFINITION_DESCRIPTION,
        mime_type="text/plain",
    )
    def user_unit_definition(user: str, type: str, name: str) -> str:
        return find_unit(
            scope="user",
            user=user,
            unit_type=type,
            name=name,
        ).definition
