# ADR 0001: Layer the MCP interface into resources, primitives, and intent workflows

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

The purpose of mcp-systemd is not to expose `systemctl` commands through MCP. The interface should represent systemd semantically and help a model operate on it at the appropriate level of abstraction.

A model sometimes needs direct access to systemd objects and atomic operations, but common administrative activities are better expressed as intents that can be implemented as deterministic workflows.

## Decision

The MCP interface will be designed in three conceptual layers:

1. **Resources**  
   Semantic representations of systemd objects and their state.

2. **Primitive operations**  
   Small, predictable operations acting on those resources. These are the low-level building blocks available to the model.

3. **Intent/workflow operations**  
   Higher-level operations representing administrative goals or use cases. Their implementation may orchestrate multiple primitive operations and checks.

The third layer is intentionally opinionated: when a well-defined workflow exists, it should provide the most direct path for the model to express the desired outcome instead of requiring the model to reconstruct the procedure itself.

## Consequences

- The public interface is not derived mechanically from `systemctl`.
- Primitive operations remain available for flexibility and composition.
- Reusable administrative knowledge can be encoded in deterministic workflows instead of relying entirely on model reasoning.
- The interface can make complex tasks more accessible to smaller models by reducing the number of decisions they must make.
