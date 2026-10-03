# AGENTS.md

## What this is
MCP server exposing systemd units as MCP resources. `src/mcp_systemd/catalog.py` is the single source of truth for unit data.

## Commands (use `uv`; deps pinned in `uv.lock`)
- Sync: `uv sync --locked`
- Run server: `uv run mcp-systemd` (FastMCP HTTP transport; default `127.0.0.1:48000`; `--config <path>` overrides `/etc/mcp-systemd/config.yaml`)
- All tests: `uv run python -m unittest discover -s tests`
- Single test: `uv run python -m unittest tests.test_catalog.UnitUriTests.test_resolves_canonical_system_uri`
- Validate eval corpus: `uv run python evals/validate.py`

There is **no** lint, typecheck, or formatter configured. Do not invent `ruff`/`mypy` commands; the checks above are the whole surface.

## Gotchas
- `pyproject.toml` declares `requires-python >=3.10`, but CI uses Python 3.13. Changing deps requires `uv lock` and committing `uv.lock`.
- CI (`.github/workflows/ci.yml`) is `workflow_dispatch` only — it does **not** run on pushes or PRs. Run checks locally before claiming success.
- Tools are gated by exposure groups. Adding/renaming a tool means updating `TOOL_GROUPS` in `tools.py`, `DEFAULT_TOOL_GROUPS` in `config.py`, and tests; unknown tool/group names make config loading or server build raise `ValueError`.
- `enable` overrides `disable` overrides groups; group `resource_api_fallback` (default on) gates `list_units`, `read_unit`, `read_unit_definition`. `list_unit_types` has no group.
- Resource identity lives in the URI, so read payloads intentionally omit the unit name. `resources/list` exposes only base unit resources, never `/definition` sub-resources.
- `find_unit_by_uri` rejects non-canonical URIs (trailing slash, query, fragment, extra path like `/definition`). Keep URIs exact.
- Supported unit types are only `service` and `timer`; other types raise.

## Conventions
- Conventional Commits, imperative, lowercase, no trailing period (`feat(scope): ...`). Branch prefixes: `feat/ fix/ docs/ refactor/ test/ chore/`.
- Design decisions live in `docs/adr/` (see `docs/adr/README.md`). Interface changes should add/update an ADR rather than silently diverge.
- `evals/` is a model-facing corpus and is only structurally validated; it is not a substitute for functional tests. New model-facing capabilities should add/update eval cases (`evals/cases/*.yaml`).
