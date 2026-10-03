# mcp-systemd

Experimental semantic MCP interface for systemd.

The MCP server is the real implementation. The systemd backend is selected from configuration: an in-memory simulated backend (default) or the host's real system manager over D-Bus.

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

The default composition uses `MockSystemd`. Setting `backend.type: dbus` composes `DbusSystemd` against the local system manager instead. Resources and Tools depend only on the domain port, so the backend can be replaced without changing the MCP interface.

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

## Property catalog

The standalone [unit property catalog](docs/property-catalog.md) maps native
D-Bus properties to public names, descriptions and JSON Schemas. The initial
catalog contains 18 bindings for services and timers. It is separate from server
configuration and is not yet loaded or exposed by the MCP server.

## Semantic evaluations

The `evals/` directory contains repeatable model-facing evaluation cases for discovery, state inspection, unit definitions, unsupported capabilities, and token-efficient behavior.

Validate the corpus with:

```bash
uv run python evals/validate.py
```

See `evals/README.md` for the case format and execution protocol.

## Tests

Run the unit and integration suites separately:

```bash
uv run python -m unittest discover -s tests/unit
uv run python -m unittest discover -s tests/integration
```

Semantic model behavior remains covered separately under `evals/`.

See `tests/README.md` for the TDD workflow and test-layer definitions.

A manual-only GitHub Actions workflow named `CI` runs the locked install, functional tests, and semantic-eval validation in a clean environment. It is not triggered by pushes or pull requests.

## Run

```bash
uv sync --locked
uv run mcp-systemd
```

Runtime dependencies are committed in `uv.lock`.

The server uses FastMCP HTTP transport.

By default it listens only on `127.0.0.1:48000`.

## Backends

The server can run against two backends, selected from configuration:

- `mock` (default): the in-memory simulated backend used for development, tests, and semantic evaluation;
- `dbus`: the real system manager over D-Bus, read-only.

```yaml
backend:
  type: mock
```

```yaml
backend:
  type: dbus
```

Backend selection is composition only. Building the server does not connect to D-Bus: the connection is lazy and happens on the first operation. Failures surface on that first operation and are never replaced by an automatic fallback to the mock.

With `dbus`, only system services and timers are supported:

- discovery (`list_units`) and fresh runtime-state reads (`read_unit`) work;
- unit definitions (`read_unit_definition`) and user managers are not implemented and fail explicitly;
- `list_unit_types` lists the supported domain unit types, not a backend capability matrix.

Capabilities are not inferred from the selected backend: tool exposure remains controlled by `tools.groups`, `tools.enable`, and `tools.disable`. The example below disables `read_unit_definition` for a D-Bus trial. Disabling the tool hides that tool only; the definition and user Resource templates still exist, and unsupported reads fail.

## Configuration

The default configuration path is `/etc/mcp-systemd/config.yaml`.

When no `--config` is given, the default path is used if it exists; if it is absent, built-in defaults are used (`mock` backend, `127.0.0.1:48000`).

An explicit path is required to exist: `uv run mcp-systemd --config ./config.yaml` exits nonzero if the file is missing or invalid, before any server is started.

Configuration is read once at startup; restart the server after changing it.

Example:

```yaml
server:
  host: 127.0.0.1
  port: 48000

backend:
  type: dbus

tools:
  disable:
    - read_unit_definition
```

`backend` is optional. A missing `backend` section, or `backend: {}`, selects `mock`. Only `type` is allowed inside `backend`; unknown keys inside `backend`, unknown root keys, and unsupported backend types are rejected. Supported values are the exact, case-sensitive strings `mock` and `dbus`.

Launch with a configuration file:

```bash
uv run mcp-systemd --config ./config.yaml
```

On startup the CLI prints the selected backend to stderr, for example `backend=dbus (local system manager)`. This announces the selection; it does not mean a D-Bus connection has been established.
