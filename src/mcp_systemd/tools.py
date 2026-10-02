from fastmcp import FastMCP

from mcp_systemd.catalog import list_unit_records, list_unit_type_records


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name="list_units",
        description=(
            "List systemd units known by the service manager. "
            "Use this to discover units or find one when its exact name is unknown."
        ),
    )
    def list_units() -> dict[str, list[dict[str, str]]]:
        return {
            "units": [unit.discovery() for unit in list_unit_records()],
        }

    @mcp.tool(
        name="list_unit_types",
        description=(
            "List supported systemd unit types and what they represent. "
            "Use this when you need to identify or understand a unit type."
        ),
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
