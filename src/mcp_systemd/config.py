from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import yaml

DEFAULT_CONFIG_PATH = Path("/etc/mcp-systemd/config.yaml")

DEFAULT_TOOL_GROUPS = {
    "resource_api_fallback": True,
}

SUPPORTED_BACKEND_TYPES = ("mock", "dbus")

_ROOT_KEYS = {"server", "tools", "backend"}


@dataclass(frozen=True)
class BackendConfig:
    type: str = "mock"

    def __post_init__(self) -> None:
        if self.type not in SUPPORTED_BACKEND_TYPES:
            raise ValueError(f"Unsupported backend type: {self.type!r}")


@dataclass(frozen=True)
class ToolExposureConfig:
    groups: Mapping[str, bool] = field(
        default_factory=lambda: dict(DEFAULT_TOOL_GROUPS)
    )
    enable: frozenset[str] = frozenset()
    disable: frozenset[str] = frozenset()

    def is_enabled(
        self,
        name: str,
        *,
        groups: frozenset[str] = frozenset(),
    ) -> bool:
        if name in self.disable:
            return False

        if name in self.enable:
            return True

        for group in groups:
            if group not in self.groups:
                raise ValueError(f"Unknown tool group: {group}")

            if not self.groups[group]:
                return False

        return True


@dataclass(frozen=True)
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 48000
    tools: ToolExposureConfig = field(default_factory=ToolExposureConfig)
    backend: BackendConfig = field(default_factory=BackendConfig)


def _parse_tool_names(value: object, field_name: str) -> frozenset[str]:
    if not isinstance(value, list):
        raise ValueError(f"tools.{field_name} must be a list")

    if not all(isinstance(name, str) and name for name in value):
        raise ValueError(
            f"tools.{field_name} must contain non-empty tool names"
        )

    return frozenset(value)


def _parse_tool_exposure(tools: dict) -> ToolExposureConfig:
    allowed_keys = {"groups", "enable", "disable"}
    unknown_keys = set(tools) - allowed_keys
    if unknown_keys:
        names = ", ".join(sorted(unknown_keys))
        raise ValueError(f"Unknown tools configuration: {names}")

    configured_groups = tools.get("groups", {})
    if not isinstance(configured_groups, dict):
        raise ValueError("tools.groups must be a mapping")

    unknown_groups = set(configured_groups) - set(DEFAULT_TOOL_GROUPS)
    if unknown_groups:
        names = ", ".join(sorted(unknown_groups))
        raise ValueError(f"Unknown tool group: {names}")

    if not all(isinstance(value, bool) for value in configured_groups.values()):
        raise ValueError("tools.groups values must be booleans")

    groups = dict(DEFAULT_TOOL_GROUPS)
    groups.update(configured_groups)

    enable = _parse_tool_names(tools.get("enable", []), "enable")
    disable = _parse_tool_names(tools.get("disable", []), "disable")

    overlap = enable & disable
    if overlap:
        names = ", ".join(sorted(overlap))
        raise ValueError(
            f"tools.enable and tools.disable overlap: {names}"
        )

    return ToolExposureConfig(
        groups=groups,
        enable=enable,
        disable=disable,
    )


def _parse_backend_config(backend: object) -> BackendConfig:
    if not isinstance(backend, dict):
        raise ValueError("backend must be a mapping")

    unknown_keys = set(backend) - {"type"}
    if unknown_keys:
        names = ", ".join(sorted(repr(key) for key in unknown_keys))
        raise ValueError(f"Unknown backend configuration: {names}")

    if "type" not in backend:
        return BackendConfig()

    return BackendConfig(type=backend["type"])


def _reject_unknown_root_keys(data: dict) -> None:
    unknown_keys = set(data) - _ROOT_KEYS
    if unknown_keys:
        names = ", ".join(sorted(repr(key) for key in unknown_keys))
        raise ValueError(f"Unknown configuration keys: {names}")


def load_config(path: Path, *, required: bool = False) -> ServerConfig:
    try:
        file = path.open("r", encoding="utf-8")
    except FileNotFoundError:
        if required:
            raise
        return ServerConfig()

    with file:
        data = yaml.safe_load(file)

    if data is None:
        return ServerConfig()

    if not isinstance(data, dict):
        raise ValueError("configuration root must be a mapping")

    _reject_unknown_root_keys(data)

    server = data.get("server", {})
    tools = data.get("tools", {})
    backend = data.get("backend", {})

    if not isinstance(server, dict):
        raise ValueError("server must be a mapping")

    if not isinstance(tools, dict):
        raise ValueError("tools must be a mapping")

    host = server.get("host", ServerConfig.host)
    port = server.get("port", ServerConfig.port)

    if not isinstance(host, str) or not host:
        raise ValueError("server.host must be a non-empty string")

    if (
        isinstance(port, bool)
        or not isinstance(port, int)
        or not 1 <= port <= 65535
    ):
        raise ValueError("server.port must be an integer between 1 and 65535")

    return ServerConfig(
        host=host,
        port=port,
        tools=_parse_tool_exposure(tools),
        backend=_parse_backend_config(backend),
    )
