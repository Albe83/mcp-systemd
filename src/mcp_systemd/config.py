from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path("/etc/mcp-systemd/config.yaml")


@dataclass(frozen=True)
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 48000
    resource_api_fallback: bool = True


def load_config(path: Path) -> ServerConfig:
    if not path.exists():
        return ServerConfig()

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError("configuration root must be a mapping")

    server = data.get("server", {})
    tools = data.get("tools", {})

    if not isinstance(server, dict):
        raise ValueError("server must be a mapping")

    if not isinstance(tools, dict):
        raise ValueError("tools must be a mapping")

    host = server.get("host", ServerConfig.host)
    port = server.get("port", ServerConfig.port)
    resource_api_fallback = tools.get(
        "resource_api_fallback",
        ServerConfig.resource_api_fallback,
    )

    if not isinstance(host, str) or not host:
        raise ValueError("server.host must be a non-empty string")

    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("server.port must be an integer between 1 and 65535")

    if not isinstance(resource_api_fallback, bool):
        raise ValueError("tools.resource_api_fallback must be a boolean")

    return ServerConfig(
        host=host,
        port=port,
        resource_api_fallback=resource_api_fallback,
    )
