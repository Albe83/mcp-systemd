# ADR 0004: Develop interface-first using a simulated systemd backend

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

The primary design risk is not whether systemd operations can be executed, but whether the MCP interface leads models toward useful and predictable behavior.

Implementing the privileged systemd adapter before validating the interface would make iteration more expensive and would expose the development host to unnecessary risk.

The MCP server itself should nevertheless be the real implementation. Replacing a simulated backend with a production backend must not require rebuilding the MCP interface.

## Decision

Development proceeds incrementally for each part of the interface:

1. Design a small portion of the MCP interface.
2. Implement that interface in the real MCP server against the simulated `Systemd` backend.
3. Add or update semantic evaluation cases that capture the intended model behavior.
4. Exercise the interface with models and observe their behavior.
5. Refine the interface based on those observations.
6. Implement the corresponding capability in the production systemd backend.
7. Repeat the cycle for the next portion.

The simulated backend is an outbound adapter behind the same domain port used by the future production implementation. It is used for development, functional tests, and semantic evaluations.

The semantic evaluation corpus is kept versioned with the interface so intended model behavior remains visible and can later be rerun across harnesses and models.

## Consequences

- The MCP surface exercised during development is the production MCP surface.
- Development and semantic evaluation do not require access to the host's real systemd manager.
- Moving from simulation to production is a composition change, not an MCP-interface rewrite.
- Backend implementation can be deferred until the corresponding interface has been validated.
