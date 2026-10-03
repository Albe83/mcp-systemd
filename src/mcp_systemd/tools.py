from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from mcp_systemd.config import ToolExposureConfig
from mcp_systemd.domain.systemd import Systemd, list_unit_types
from mcp_systemd.mcp_unit import (
    parse_unit_uri,
    unit_content,
    unit_discovery,
)


READ_ONLY_CLOSED_WORLD = ToolAnnotations(
    readOnlyHint=True,
    openWorldHint=False,
)

RESOURCE_API_FALLBACK = frozenset({"resource_api_fallback"})

TOOL_GROUPS = {
    "list_units": RESOURCE_API_FALLBACK,
    "read_unit": RESOURCE_API_FALLBACK,
    "read_unit_definition": RESOURCE_API_FALLBACK,
    "list_unit_types": frozenset(),
}

TOOL_NAMES = frozenset(TOOL_GROUPS)


def _validate_tool_overrides(config: ToolExposureConfig) -> None:
    unknown_tools = (config.enable | config.disable) - TOOL_NAMES
    if unknown_tools:
        names = ", ".join(sorted(unknown_tools))
        raise ValueError(f"Unknown tool name in configuration: {names}")


def register_tools(
    mcp: FastMCP,
    systemd: Systemd,
    *,
    exposure: ToolExposureConfig | None = None,
) -> None:
    exposure = exposure or ToolExposureConfig()
    _validate_tool_overrides(exposure)

    if exposure.is_enabled(
        "list_units",
        groups=TOOL_GROUPS["list_units"],
    ):
        @mcp.tool(
            name="list_units",
            description=(
                "List systemd units known by a service manager. "
                "Use this to discover units or find one when its exact name is unknown."
            ),
            annotations=READ_ONLY_CLOSED_WORLD,
        )
        async def list_units_tool(
            type: Annotated[
                str | None,
                "Unit type; omit for all supported types.",
            ] = None,
            user: Annotated[
                str | None,
                "User manager; omit for the system manager.",
            ] = None,
        ) -> dict[str, list[dict[str, str]]]:
            scope = "user" if user is not None else "system"
            units = await systemd.list_units(
                unit_type=type,
                scope=scope,
                user=user,
            )
            return {
                "units": [
                    unit_discovery(unit)
                    for unit in units
                ],
            }

    if exposure.is_enabled(
        "read_unit",
        groups=TOOL_GROUPS["read_unit"],
    ):
        @mcp.tool(
            name="read_unit",
            description=(
                "Read a systemd unit's current state from its resource URI. "
                "Use this for runtime-state questions."
            ),
            annotations=READ_ONLY_CLOSED_WORLD,
        )
        async def read_unit(
            uri: Annotated[str, "Base unit resource URI."],
        ) -> dict[str, str]:
            unit = await systemd.get_unit(parse_unit_uri(uri))
            return unit_content(unit)

    if exposure.is_enabled(
        "read_unit_definition",
        groups=TOOL_GROUPS["read_unit_definition"],
    ):
        @mcp.tool(
            name="read_unit_definition",
            description=(
                "Read a systemd unit's definition and drop-ins from its resource URI. "
                "Use this for configuration questions."
            ),
            annotations=READ_ONLY_CLOSED_WORLD,
        )
        async def read_unit_definition(
            uri: Annotated[str, "Base unit resource URI."],
        ) -> str:
            return await systemd.get_unit_definition(
                parse_unit_uri(uri)
            )

    if exposure.is_enabled(
        "list_unit_types",
        groups=TOOL_GROUPS["list_unit_types"],
    ):
        @mcp.tool(
            name="list_unit_types",
            description=(
                "List supported systemd unit types and what they represent. "
                "Use this when you need to identify or understand a unit type."
            ),
            annotations=READ_ONLY_CLOSED_WORLD,
        )
        def list_unit_types_tool() -> dict[str, list[dict[str, str]]]:
            return {
                "types": [
                    {
                        "name": unit_type.name,
                        "description": unit_type.description,
                    }
                    for unit_type in list_unit_types()
                ],
            }
