# ADR 0001: Layer the interface into resources, primitives, and intent workflows

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

The purpose of mcp-systemd is not to expose `systemctl` commands through MCP. The interface should represent systemd semantically and help a model operate on it at the appropriate level of abstraction.

A model needs semantic representations of systemd objects and goal-oriented operations. Internally, deterministic workflows may require lower-level systemd primitives.

## Decision

The design uses three conceptual layers:

1. **Resources**  
   Semantic representations of systemd objects and their state.

2. **Primitive operations**  
   Small, predictable operations on the systemd domain. They are implementation building blocks and may be exposed through MCP only when doing so adds distinct model-facing value.

3. **Intent/workflow operations**  
   Higher-level operations representing administrative goals or use cases. Their implementation may orchestrate multiple primitive operations and checks.

The intent layer is deliberately opinionated: when a deterministic workflow can express the user's desired outcome, the model should not be required to reconstruct that procedure from primitives.

## Consequences

- The public interface is not derived mechanically from `systemctl`.
- Primitive operations can exist behind the application boundary without consuming model context.
- A primitive can still become an MCP Tool when there is a real model-facing use case for it.
- Reusable administrative knowledge can be encoded in deterministic workflows instead of relying entirely on model reasoning.
- The interface can make complex tasks more accessible to smaller models by reducing the number of decisions they must make.
