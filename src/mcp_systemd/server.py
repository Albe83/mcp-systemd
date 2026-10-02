import argparse
from pathlib import Path

from fastmcp import FastMCP

from mcp_systemd.config import DEFAULT_CONFIG_PATH, ServerConfig, load_config
from mcp_systemd.resources import register_resources
from mcp_systemd.tools import register_tools


def build_server(config: ServerConfig | None = None) -> FastMCP:
    config = config or ServerConfig()

    mcp = FastMCP("mcp-systemd")
    register_resources(mcp)
    register_tools(
        mcp,
        resource_api_fallback=config.resource_api_fallback,
    )
    return mcp


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
    mcp = build_server(config)
    mcp.run(transport="http", host=config.host, port=config.port)


if __name__ == "__main__":
    main()
