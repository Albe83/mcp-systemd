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

The server uses FastMCP HTTP transport.

By default it listens only on `127.0.0.1:48000`.

## Configuration

The default configuration path is:

```text
/etc/mcp-systemd/config.yaml
```

If the file does not exist, the secure defaults are used.

Minimal configuration:

```yaml
server:
  host: 127.0.0.1
  port: 48000
```

A different configuration file can be selected explicitly:

```bash
uv run mcp-systemd --config ./config.yaml
```

See `config.example.yaml` for the current configuration surface.
