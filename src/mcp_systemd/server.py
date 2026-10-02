from fastmcp import FastMCP

mcp = FastMCP("mcp-systemd")


def _mock_unit(
    *,
    scope: str,
    unit_type: str,
    name: str,
    user: str | None = None,
) -> dict[str, object]:
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


@mcp.resource("systemd://unit/system/service/{name}")
def system_service(name: str) -> dict[str, object]:
    """Return a mock system-scoped service."""
    return _mock_unit(scope="system", unit_type="service", name=name)


@mcp.resource("systemd://unit/system/timer/{name}")
def system_timer(name: str) -> dict[str, object]:
    """Return a mock system-scoped timer."""
    return _mock_unit(scope="system", unit_type="timer", name=name)


@mcp.resource("systemd://unit/user/{user}/service/{name}")
def user_service(user: str, name: str) -> dict[str, object]:
    """Return a mock user-scoped service."""
    return _mock_unit(scope="user", unit_type="service", name=name, user=user)


@mcp.resource("systemd://unit/user/{user}/timer/{name}")
def user_timer(user: str, name: str) -> dict[str, object]:
    """Return a mock user-scoped timer."""
    return _mock_unit(scope="user", unit_type="timer", name=name, user=user)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
