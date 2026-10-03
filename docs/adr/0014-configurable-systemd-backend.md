# ADR 0014: Select the systemd backend from configuration

- **Status:** Accepted
- **Date:** 2026-10-03

## Context

`server.py` is the composition root and already supports injecting a `Systemd` adapter, but the CLI always composed `MockSystemd`. Running the real D-Bus adapter required editing code or constructing the server programmatically.

The simulator must remain the safe default, while the real backend must be selectable through the same normal launch path (`uv run mcp-systemd --config ...`) without introducing a plugin framework.

## Decision

The backend is selected from the existing YAML configuration through a top-level `backend` mapping:

```yaml
backend:
  type: mock   # or: dbus
```

- `mock` (default) composes `MockSystemd`.
- `dbus` composes `DbusSystemd` against the local system manager.
- A missing `backend` section, or `backend: {}`, selects `mock`.
- Only `type` is allowed; null, scalar, or list sections, unknown keys, unknown root keys, and any value other than the exact strings `mock`/`dbus` are rejected with `ValueError`.

`config.py` models this with a frozen `BackendConfig` (runtime-validated, including direct construction) added to `ServerConfig`. It does not import any backend class.

`server.py` keeps a small private factory `_build_backend(BackendConfig)` with explicit branches. `build_server` uses `ServerConfig()` only when the argument is `None`, builds the selected backend only when no adapter was injected, and otherwise uses the injected adapter unchanged (`is None`, not truthiness). The same adapter instance is passed to Resources and Tools.

D-Bus connection stays lazy: selecting `dbus`, or building the server, does not open a bus. Failures occur on the first operation and propagate; there is no fallback to `mock`.

The CLI defaults `--config` to `None`:

- no `--config` loads the default path with `required=False`;
- an explicit `--config PATH` loads `PATH` with `required=True`, even when it equals the default path.

An explicit missing or invalid file exits nonzero before the server is built or run. On startup the CLI prints the selected backend to stderr. `build_server` does not print.

Backend selection does not change tool exposure. `ToolExposureConfig` remains authoritative; capability gaps (unit definitions, user managers) fail explicitly rather than being hidden automatically.

## Consequences

- The real backend runs through the ordinary CLI with a configuration file.
- The simulator stays the default, so development and tests never touch the host's systemd manager unless requested.
- In-process callers can still inject any `Systemd` adapter, which takes precedence over configuration.
- Configuration errors fail fast instead of silently selecting the mock backend.
- Lazy connection keeps startup side-effect free; failures are observable on first use.
- New backends extend the factory and the allowed `BackendConfig` values without changing the MCP Resources or Tools.
