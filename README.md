# mcp-systemd

Experimental semantic MCP interface for systemd.

This first version is intentionally a **mock**: it exposes service and timer resources but does not talk to systemd or perform any action.

## Resource templates

```text
systemd://unit/system/service/{name}
systemd://unit/system/timer/{name}

systemd://unit/user/{user}/service/{name}
systemd://unit/user/{user}/timer/{name}
```

## Run

```bash
uv sync
uv run mcp-systemd
```

The server uses FastMCP's default STDIO transport.
