# ADR 0004: Develop interface-first using TDD and a simulated systemd backend

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

The primary design risk is not whether systemd operations can be executed, but whether the MCP interface leads models toward useful and predictable behavior.

Implementing the privileged systemd adapter before validating the interface would make iteration more expensive and would expose the development host to unnecessary risk.

The MCP server itself should nevertheless be the real implementation. Replacing a simulated backend with a production backend must not require rebuilding the MCP interface.

Code-level correctness and model-facing semantic quality are different concerns. Both need explicit feedback loops.

## Decision

Development uses two complementary feedback loops.

### Code-level TDD

Behavioral code changes follow Red-Green-Refactor:

1. write the smallest unit test that expresses the desired behavior and observe it fail;
2. implement the minimum code required to make the test pass;
3. refactor while keeping the suite green;
4. add an integration test when the behavior crosses an architectural boundary.

Bug fixes start with a reproducing test whenever practical.

Unit tests should target domain behavior, configuration, mapping, or an adapter in isolation. Integration tests verify collaboration across the MCP and composition boundaries.

### Interface-first semantic evaluation

For each model-facing interface slice:

1. define the semantic MCP contract;
2. implement it in the real MCP server against the simulated `Systemd` backend using the TDD loop above;
3. add or update semantic evaluation cases that capture the intended model behavior;
4. exercise the interface with models and observe their behavior;
5. refine the interface based on those observations;
6. implement the corresponding capability in the production systemd backend;
7. repeat the cycle for the next portion.

The simulated backend is an outbound adapter behind the same domain port used by the future production implementation. It is used for development, functional tests, and semantic evaluations.

The semantic evaluation corpus is kept versioned with the interface so intended model behavior remains visible and can later be rerun across harnesses and models.

## Consequences

- New deterministic behavior is specified by executable tests before implementation.
- Refactoring is protected by fast unit tests.
- Integration tests focus on architectural boundaries rather than duplicating unit coverage.
- Semantic evaluations remain focused on model decisions rather than code correctness.
- The MCP surface exercised during development is the production MCP surface.
- Development and semantic evaluation do not require access to the host's real systemd manager.
- Moving from simulation to production is a composition change, not an MCP-interface rewrite.
- Backend implementation can be deferred until the corresponding interface has been validated.
