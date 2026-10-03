# Tests

The test suite is split by purpose.

## Unit tests

`tests/unit/` contains fast, deterministic tests for one unit of behavior at a time.

Typical subjects:

- domain invariants and behavior;
- configuration logic;
- MCP URI and serialization mapping;
- one backend adapter in isolation.

Unit tests should not assemble the complete FastMCP server and should not require the host's real systemd manager.

Prefer small fakes that implement a domain port over patching internal implementation details.

Run:

```bash
uv run python -m unittest discover -s tests/unit
```

## Integration tests

`tests/integration/` verifies collaboration across boundaries, such as:

- FastMCP Resource providers;
- Tool/Resource registration;
- composition-root wiring;
- exposure of the assembled MCP surface.

The current integration suite still uses simulated backends and therefore remains safe to run on a development machine.

Run:

```bash
uv run python -m unittest discover -s tests/integration
```

## Semantic evaluations

`evals/` is separate from the code-level test suite.

Semantic evaluations answer a different question: whether the model understands and uses the MCP interface as intended.

They do not replace unit or integration tests.

## TDD workflow

For a behavioral change:

1. write the smallest unit test that expresses the new behavior and see it fail;
2. implement the minimum code required to make it pass;
3. refactor while keeping the test green;
4. add an integration test only when the change crosses an architectural boundary;
5. add or update semantic eval cases when the model-facing contract changes.

Bug fixes start with a reproducing test whenever practical.
