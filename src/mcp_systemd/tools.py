from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from mcp_systemd.catalog import (
    find_unit_by_uri,
    list_unit_records,
    list_unit_type_records,
)
from mcp_systemd.config import ToolExposureConfig


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
        def list_units(
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
            return {
                "units": [
                    unit.discovery()
                    for unit in list_unit_records(
                        unit_type=type,
                        scope=scope,
                        user=user,
                    )
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
        def read_unit(
            uri: Annotated[str, "Base unit resource URI."],
        ) -> dict[str, str]:
            return find_unit_by_uri(uri).content()

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
        def read_unit_definition(
            uri: Annotated[str, "Base unit resource URI."],
        ) -> str:
            return find_unit_by_uri(uri).definition

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
        def list_unit_types() -> dict[str, list[dict[str, str]]]:
            return {
                "types": [
                    {
                        "name": unit_type.name,
                        "description": unit_type.description,
                    }
                    for unit_type in list_unit_type_records()
                ],
            }
