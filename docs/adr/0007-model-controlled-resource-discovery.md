# ADR 0007: Provide model-controlled discovery for resource-oriented interfaces

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

MCP resources provide a semantic representation of objects, but resources are primarily client/application-controlled. An MCP client can list resource templates and concrete resources, yet a model is not guaranteed to receive that catalog or to have an explicit and predictable mechanism for discovering it.

For an agent-oriented interface this creates a usability gap: the server may expose a well-designed resource model while the model still does not know which resources exist, which resource types are valid, or how to discover them.

Tools, by contrast, are model-controlled capabilities. Their names, descriptions, and schemas are normally exposed directly to the model.

## Decision

When important resource-oriented capabilities would otherwise be difficult for a model to discover, mcp-systemd exposes small model-controlled discovery tools.

The initial discovery tools are:

```text
list_units
list_unit_types
```

### `list_units`

`list_units` exposes the same logical unit catalog as `resources/list`.

Both interfaces must share the same underlying discovery code and semantics:

```text
                  unit catalog
                  /          \
                 /            \
        resources/list      list_units
        client-facing       model-controlled
```

The tool must not implement an independent discovery path that could disagree with `resources/list`.

Its semantics remain those defined for resource discovery: the logical equivalent of `systemctl list-units --all`, restricted to the unit types supported by mcp-systemd.

### `list_unit_types`

`list_unit_types` exposes the unit types currently supported by the server together with a concise semantic description of each type.

Initially:

```text
service
timer
```

This makes the interface self-describing for the model instead of requiring supported types and their meaning to be embedded in an external agent prompt.

### Resources remain the object model

Discovery tools help the model find and understand resources; they do not replace the resources themselves.

The server therefore does not introduce a parallel `read_unit` tool at this stage. Reading a unit remains a resource operation. Tool duplication should only be introduced later if a concrete harness or model requirement demonstrates that it is necessary.

## General design principle

For resource-oriented MCP servers:

1. use Resources to model domain objects and their semantic representations;
2. identify information the model needs in order to navigate or understand that resource model;
3. when that information is not predictably available to the model, expose a small model-controlled discovery or introspection Tool;
4. share underlying logic between client-facing resource discovery and model-facing tool discovery;
5. avoid duplicating resource read or mutation semantics as tools without a demonstrated need;
6. prefer self-describing interfaces over hidden assumptions in agent prompts.

## Consequences

- Models have an explicit and predictable path for discovering unit resources.
- Smaller models do not need to infer valid resource types from URI templates alone.
- Clients can continue to use native MCP resource discovery independently of the model.
- Resource and tool views cannot intentionally diverge because they share the same catalog abstraction.
- The MCP interface becomes more portable across harnesses with different resource-injection behavior.
- The pattern can be reused when designing other resource-oriented MCP servers.
