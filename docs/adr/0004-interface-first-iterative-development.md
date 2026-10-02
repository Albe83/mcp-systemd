# ADR 0004: Develop interface-first using an MCP stub before backend implementation

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

The primary design risk is not whether systemd operations can be executed, but whether the MCP interface leads models toward useful and predictable behavior.

Implementing the systemd backend before validating the interface would make iteration more expensive and could prematurely couple the public contract to implementation details.

## Decision

Development will proceed incrementally for each part of the interface:

1. Design a small portion of the MCP interface.
2. Implement that interface as an MCP stub/mock without real systemd actions.
3. Exercise the interface with models and observe their behavior.
4. Refine the interface based on those observations.
5. Implement the real actions behind the validated interface.
6. Repeat the cycle for the next portion.

Backend implementation is deliberately deferred until the corresponding interface has been exercised as an MCP contract.

## Consequences

- Interface design can evolve cheaply before systemd-specific implementation work is committed.
- Model behavior becomes an explicit input to API design.
- The project can validate whether resources, primitives, and workflows are understandable before connecting them to privileged host operations.
- Early versions may expose complete MCP contracts whose implementations are intentionally non-operative or simulated.
