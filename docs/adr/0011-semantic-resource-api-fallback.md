# ADR 0011: Provide semantic Resource API fallback tools

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

MCP defines Resource discovery and reading as client-controlled protocol operations.

Some harnesses expose these operations to the model through generated tools or equivalent mechanisms, while others may not. mcp-systemd should remain usable across harnesses without making its domain model depend on a specific client implementation.

A generic tool such as `read_resource` would mirror MCP protocol mechanics into the model-facing interface. This would expose infrastructure vocabulary rather than systemd semantics and would increase the model's decision surface.

## Decision

Resources remain the canonical representation of systemd units.

mcp-systemd also provides optional semantic fallback tools for the parts of the Resource API the model needs directly:

```text
list_units
read_unit
read_unit_definition
```

These tools are domain-specific projections of the Resource model, not an alternative object model.

### `read_unit`

`read_unit(uri)` accepts the URI of a base unit resource:

```text
systemd://system/unit/service/sshd
systemd://user/albe/unit/service/cortana
```

and returns the same compact unit representation exposed by reading that base Resource.

### `read_unit_definition`

`read_unit_definition(uri)` accepts the same base unit URI and returns the semantic definition view for that unit.

The caller does not need to construct or know the `/definition` sub-resource URI. The tool encapsulates that relationship because the model's intent is to read the unit definition, not to navigate Resource protocol structure.

### No generic Resource bridge

mcp-systemd does not expose generic protocol-shaped tools such as:

```text
list_resources
read_resource
list_resource_templates
```

The model-facing fallback remains expressed in systemd domain terms.

### Deployment policy

The semantic Resource API fallback is enabled by default.

It can be disabled with:

```yaml
tools:
  resource_api_fallback: false
```

When disabled, the following overlapping tools are not exposed:

```text
list_units
read_unit
read_unit_definition
```

The Resources themselves remain available through MCP.

`list_unit_types` is not part of this fallback class because it exposes mcp-systemd-specific semantic introspection rather than duplicating a Resource protocol operation.

This allows deployments whose harness already provides model-controlled Resource listing and reading to reduce duplicate tools, token cost, and tool-selection ambiguity.

## General design principle

When portability across MCP harnesses requires a fallback for client-controlled primitives:

1. keep the protocol-native object model canonical;
2. expose only the model-facing operations needed for the domain;
3. name fallback operations in domain language rather than protocol language;
4. route native and fallback access through the same underlying representation;
5. make overlapping fallback capabilities removable at deployment time.

## Consequences

- mcp-systemd does not depend on a harness-specific Resource projection.
- Models can discover and read units even when the harness does not expose Resource operations directly.
- Harnesses with native Resource support can remove overlapping tools.
- The model never needs a generic `read_resource` abstraction.
- Sub-resource structure can evolve without requiring the fallback tool contract to expose URI navigation details.
