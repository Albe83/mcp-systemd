from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path("/etc/mcp-systemd/config.yaml")


@dataclass(frozen=True)
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 48000


def load_config(path: Path) -> ServerConfig:
    if not path.exists():
        return ServerConfig()

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    server = data.get("server", {})
    host = server.get("host", ServerConfig.host)
    port = server.get("port", ServerConfig.port)

    if not isinstance(host, str) or not host:
        raise ValueError("server.host must be a non-empty string")

    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("server.port must be an integer between 1 and 65535")

    return ServerConfig(host=host, port=port)
