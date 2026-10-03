# AGENTS.md

## What this is
MCP server exposing systemd units as MCP resources. The architecture is a small hexagonal boundary: the MCP adapter (Resources/Tools) depends on a `Systemd` port, concrete adapters live in `backends/`, and `server.py` is the composition root.

- `src/mcp_systemd/domain/` — systemd-facing model and the `Systemd` port. No MCP, FastMCP, URI, or serialization concepts here.
- `src/mcp_systemd/mcp_unit.py` — MCP identity/serialization: `UnitRef` <-> `systemd://...` URI and unit -> payload.
- `src/mcp_systemd/backends/` — adapters implementing the port; fixtures live in `backends/mock.py`.
- `src/mcp_systemd/resources.py` / `tools.py` — FastMCP adapter, depending only on the port.

## Commands (use `uv`; deps pinned in `uv.lock`)
- Sync: `uv sync --locked`
- Run server: `uv run mcp-systemd` (FastMCP HTTP transport; default `127.0.0.1:48000`; `--config <path>` overrides `/etc/mcp-systemd/config.yaml`)
- Unit tests: `uv run python -m unittest discover -s tests/unit`
- Integration tests: `uv run python -m unittest discover -s tests/integration`
- Single test: `uv run python -m unittest tests.unit.test_mcp_unit.UnitUriTests.test_round_trip_system_unit`
- Validate eval corpus: `uv run python evals/validate.py`
- Python 3.10 checks (throwaway container, host-independent): `Containerfiles/verify-python.sh`

There is **no** lint, typecheck, or formatter configured. Do not invent `ruff`/`mypy` commands; the checks above are the whole surface.

## Gotchas
- `pyproject.toml` declares `requires-python >=3.10`, but CI uses Python 3.13. Changing deps requires `uv lock` and committing `uv.lock`. The declared minimum Python can be verified without a host interpreter via `Containerfiles/verify-python.sh` (throwaway container; keeps the repo read-only).
- CI (`.github/workflows/ci.yml`) is `workflow_dispatch` only — it does **not** run on pushes or PRs. Run checks locally before claiming success.
- Preserve the boundary: `domain/` must not import FastMCP, MCP types, URIs, or backend code; URI parsing/serialization belongs in `mcp_unit.py`. `systemd` is an injectable port, so tests compose a fake backend instead of mocking FastMCP.
- The `Systemd` port and the resource/tool handlers are `async`; async tests subclass `unittest.IsolatedAsyncioTestCase`. Discovery stores only a `UnitRef` and reads call `get_unit(ref)` fresh, so state is not frozen at discovery time (ADR 0013) — do not cache `Unit` objects in the provider.
- Adding a unit type means a new `domain/unit_<type>.py` (a `<Type>Unit` dataclass enforcing its own `ref.type`) plus registering it in `UNIT_TYPES` in `domain/systemd.py`. Supported types are only `service` and `timer`; other names raise `ValueError`.
- Tools are gated by exposure groups. Adding/renaming a tool means updating `TOOL_GROUPS` in `tools.py`, `DEFAULT_TOOL_GROUPS` in `config.py`, and tests; unknown tool/group names make config loading or server build raise `ValueError`.
- `enable` overrides `disable` overrides groups; group `resource_api_fallback` (default on) gates `list_units`, `read_unit`, `read_unit_definition`. `list_unit_types` has no group.
- Resource identity lives in the URI, so read payloads intentionally omit the unit name. `resources/list` exposes only base unit resources, never `/definition` sub-resources.
- `mcp_unit.parse_unit_uri` rejects non-canonical URIs (trailing slash, query, fragment, extra path like `/definition`). Keep URIs exact.

## Conventions
- Conventional Commits, imperative, lowercase, no trailing period (`feat(scope): ...`). Branch prefixes: `feat/ fix/ docs/ refactor/ test/ chore/`.
- Design decisions live in `docs/adr/` (see `docs/adr/README.md`). Interface changes should add/update an ADR rather than silently diverge.
- Tests are layered (see `tests/README.md`): `tests/unit/` for domain/config/serialization/one adapter, `tests/integration/` for FastMCP wiring and the assembled surface. Behavioral changes follow red-green-refactor: failing unit test first, then minimal code; add an integration test only when crossing a boundary.
- `evals/` is a model-facing corpus and is only structurally validated; it is not a substitute for tests. New or changed model-facing contracts should add/update eval cases (`evals/cases/*.yaml`).
