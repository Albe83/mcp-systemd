from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from mcp_systemd.catalog import list_unit_records, list_unit_type_records


READ_ONLY_CLOSED_WORLD = ToolAnnotations(
    readOnlyHint=True,
    openWorldHint=False,
)


def register_tools(mcp: FastMCP) -> None:
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
