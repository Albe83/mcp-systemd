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

For each represented systemd manager, discovery follows the logical semantics of `systemctl list-units --all`, restricted to supported unit types. `resources/list` exposes the combined concrete Resource catalog across the represented managers on the host.

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

## Model-facing tools

The server exposes semantic tools that make the Resource model usable even when an MCP harness does not expose Resource operations directly to the model:

- `list_units(type?, user?)` discovers unit Resources;
- `read_unit(uri)` reads the compact current state of a unit;
- `read_unit_definition(uri)` reads its definition and drop-ins;
- `list_unit_types()` describes the unit types supported by mcp-systemd.

`read_unit` and `read_unit_definition` both accept the canonical base unit Resource URI. The model does not need to construct sub-resource URIs.

The Resources remain canonical. The first three tools are a semantic fallback and can be disabled when the deployment harness already gives the model equivalent access to concrete Resource discovery, Resource Templates or equivalent sub-resource discovery, and Resource reading.

## Semantic evaluations

The `evals/` directory contains repeatable model-facing evaluation cases for discovery, state inspection, unit definitions, unsupported capabilities, and token-efficient behavior.

Validate the corpus with:

```bash
uv run python evals/validate.py
```

See `evals/README.md` for the case format and execution protocol.

## Functional checks

Run the lightweight functional test suite with:

```bash
uv run python -m unittest discover -s tests
```

A manual-only GitHub Actions workflow named `CI` runs the locked install, functional tests, and semantic-eval validation in a clean environment. It is not triggered by pushes or pull requests.

## Run

```bash
uv sync --locked
uv run mcp-systemd
```

Runtime dependencies are committed in `uv.lock`.

The server uses FastMCP HTTP transport.

By default it listens only on `127.0.0.1:48000`.

## Configuration

The default configuration path is:

```text
/etc/mcp-systemd/config.yaml
```

If the file does not exist, the secure defaults are used.

Example:

```yaml
server:
  host: 127.0.0.1
  port: 48000

tools:
  resource_api_fallback: true
```

Set `tools.resource_api_fallback` to `false` only when the harness provides equivalent model-controlled Resource discovery, sub-resource/template discovery, and reading. Native MCP Resources remain exposed, and `list_unit_types` remains available.

A different configuration file can be selected explicitly:

```bash
uv run mcp-systemd --config ./config.yaml
```

See `config.example.yaml` for the current configuration surface.
