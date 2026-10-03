import argparse
import sys
from pathlib import Path

from fastmcp import FastMCP

from mcp_systemd.backends.dbus import DbusSystemd
from mcp_systemd.backends.mock import MockSystemd
from mcp_systemd.config import (
    DEFAULT_CONFIG_PATH,
    BackendConfig,
    ServerConfig,
    load_config,
)
from mcp_systemd.domain.systemd import Systemd
from mcp_systemd.resources import register_resources
from mcp_systemd.tools import register_tools


def _build_backend(config: BackendConfig) -> Systemd:
    if config.type == "mock":
        return MockSystemd()

    if config.type == "dbus":
        return DbusSystemd()

    raise ValueError(f"Unsupported backend type: {config.type!r}")


def build_server(
    config: ServerConfig | None = None,
    *,
    systemd: Systemd | None = None,
) -> FastMCP:
    if config is None:
        config = ServerConfig()

    if systemd is None:
        systemd = _build_backend(config.backend)

    mcp = FastMCP("mcp-systemd")
    register_resources(mcp, systemd)
    register_tools(
        mcp,
        systemd,
        exposure=config.tools,
    )
    return mcp


def _describe_backend(backend: BackendConfig) -> str:
    if backend.type == "dbus":
        return "backend=dbus (local system manager)"
    return f"backend={backend.type}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=f"configuration file (default: {DEFAULT_CONFIG_PATH})",
    )
    args = parser.parse_args()

    try:
        if args.config is None:
            config = load_config(DEFAULT_CONFIG_PATH, required=False)
        else:
            config = load_config(args.config, required=True)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    mcp = build_server(config)
    print(_describe_backend(config.backend), file=sys.stderr)
    mcp.run(transport="http", host=config.host, port=config.port)


if __name__ == "__main__":
    main()
