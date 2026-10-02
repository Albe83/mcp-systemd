from fastmcp import FastMCP

mcp = FastMCP("mcp-systemd")

SUPPORTED_TYPES = {"service", "timer"}


def _mock_unit(
    *,
    scope: str,
    unit_type: str,
    name: str,
    user: str | None = None,
) -> dict[str, object]:
    if unit_type not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported unit type: {unit_type}")

    unit: dict[str, object] = {
        "name": name,
        "type": unit_type,
        "scope": scope,
        "mock": True,
        "state": {
            "active": "active",
            "sub": "running" if unit_type == "service" else "waiting",
        },
    }

    if user is not None:
        unit["user"] = user

    return unit


@mcp.resource("systemd://unit/system/{type}/{name}")
def system_unit(type: str, name: str) -> dict[str, object]:
    """Return a mock system-scoped unit."""
    return _mock_unit(scope="system", unit_type=type, name=name)


@mcp.resource("systemd://unit/user/{user}/{type}/{name}")
def user_unit(user: str, type: str, name: str) -> dict[str, object]:
    """Return a mock user-scoped unit."""
    return _mock_unit(scope="user", unit_type=type, name=name, user=user)


def main() -> None:
    mcp.run(transport="http", host="127.0.0.1", port=48000)


if __name__ == "__main__":
    main()
