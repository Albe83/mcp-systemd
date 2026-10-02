# mcp-systemd

Experimental semantic MCP interface for systemd.

This first version is intentionally a **mock**: it exposes systemd unit resources but does not talk to systemd or perform any action.

## Resource templates

```text
systemd://unit/system/{type}/{name}
systemd://unit/user/{user}/{type}/{name}
```

The initial mock supports `service` and `timer` as unit types.

## Run

```bash
uv sync
uv run mcp-systemd
```

The server uses FastMCP's default STDIO transport.
