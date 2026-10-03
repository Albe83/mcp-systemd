# mcp-systemd

Experimental semantic MCP interface for systemd.

The MCP server is the real implementation. During interface development it is wired to an in-memory simulated systemd backend instead of the host's real systemd manager.

## Architecture

The server uses a small hexagonal boundary:

```text
MCP Resources / Tools
        |
        v
   domain.Systemd
        |
        v
    backend adapter
```

The domain model and `Systemd` port live under `src/mcp_systemd/domain/`. Concrete adapters live under `src/mcp_systemd/backends/`.

The default development composition uses `MockSystemd`. Resources and Tools depend only on the domain port, so a future production backend can replace the mock without changing the MCP interface.

MCP URIs and payload serialization remain outside the domain model.

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

The Resources remain canonical. The first three tools are a semantic fallback and belong to the `resource_api_fallback` exposure group.

## Tool exposure

Tool exposure is configured independently from MCP Tool Annotations.

Each tool can belong to zero or more exposure groups. Groups act as feature flags for the model-facing tool surface, and individual tools can be enabled or disabled as explicit overrides.

Example:

```yaml
tools:
  groups:
    resource_api_fallback: true

  enable: []
  disable: []
```

The default `resource_api_fallback` group contains:

```text
list_units
read_unit
read_unit_definition
```

Set the group to `false` when the harness already provides equivalent model-controlled Resource discovery, sub-resource/template discovery, and reading.

An explicit per-tool override takes precedence over group membership:

```yaml
tools:
  groups:
    resource_api_fallback: false

  enable:
    - read_unit

  disable:
    - list_unit_types
```

A tool cannot appear in both `enable` and `disable`.

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

If the file does not exist, the defaults are used.

Example:

```yaml
server:
  host: 127.0.0.1
  port: 48000

tools:
  groups:
    resource_api_fallback: true
  enable: []
  disable: []
```

A different configuration file can be selected explicitly:

```bash
uv run mcp-systemd --config ./config.yaml
```

See `config.example.yaml` for the current configuration surface.
