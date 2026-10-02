# mcp-systemd

Experimental semantic MCP interface for systemd.

This first version is intentionally a **mock**: it exposes systemd unit resources but does not talk to systemd or perform any action.

## Resource templates

```text
systemd://system/unit/{type}/{name}
systemd://user/{user}/unit/{type}/{name}

systemd://system/unit/{type}/{name}/definition
systemd://user/{user}/unit/{type}/{name}/definition
```

The initial mock supports `service` and `timer` as unit types.

`resources/list` exposes a mock catalog representing the logical equivalent of `systemctl list-units --all`, restricted to the supported unit types.

Reading a unit resource returns compact runtime state:

```json
{
  "description": "OpenSSH server daemon",
  "load_state": "loaded",
  "active_state": "active",
  "sub_state": "running"
}
```

The URI carries the unit identity, so the payload does not repeat the unit name.

The `/definition` sub-resource returns the unit file and drop-ins as text. It is separate because configuration content can be much larger and is not needed for most state-oriented decisions.

## Discovery tools

Two small tools make the resource model explicitly discoverable by models:

- `list_units` exposes the same unit catalog as `resources/list`;
- `list_unit_types` lists the supported unit types and their semantic descriptions.

The tools are for discovery and introspection. Unit resources remain the canonical object representation.

## Semantic evaluations

The `evals/` directory contains repeatable model-facing evaluation cases for discovery, state inspection, unit definitions, unsupported capabilities, and token-efficient behavior.

Validate the corpus with:

```bash
uv run python evals/validate.py
```

See `evals/README.md` for the case format and execution protocol.

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
