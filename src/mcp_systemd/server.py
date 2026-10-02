import argparse
from pathlib import Path

from fastmcp import FastMCP

from mcp_systemd.config import DEFAULT_CONFIG_PATH, load_config
from mcp_systemd.resources import MockUnitProvider, find_unit

SYSTEM_UNIT_DESCRIPTION = (
    "A systemd unit managed by the system service manager. "
    "Service units represent processes controlled and supervised by systemd; "
    "timer units schedule time-based activation of other units."
)

USER_UNIT_DESCRIPTION = (
    "A systemd unit managed by a user's service manager. "
    "Service units represent processes controlled and supervised by systemd; "
    "timer units schedule time-based activation of other units."
)

mcp = FastMCP("mcp-systemd")
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"configuration file (default: {DEFAULT_CONFIG_PATH})",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    mcp.run(transport="http", host=config.host, port=config.port)


if __name__ == "__main__":
    main()
