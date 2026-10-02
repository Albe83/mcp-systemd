from fastmcp import FastMCP

from mcp_systemd.catalog import list_unit_records, list_unit_type_records


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name="list_units",
        description=(
            "List systemd units currently known by the service manager. "
            "This is the model-controlled discovery view of the same catalog exposed "
            "through resources/list, logically equivalent to systemctl list-units --all "
            "and restricted to the unit types supported by this server."
        ),
    )
    def list_units() -> dict[str, list[dict[str, str]]]:
        return {
            "units": [unit.discovery() for unit in list_unit_records()],
        }

    @mcp.tool(
        name="list_unit_types",
        description=(
            "List the systemd unit types supported by this server and explain what each "
            "type represents. Use this to understand valid unit types before discovering "
            "or addressing unit resources."
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
