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

`read_unit(uri)` accepts the canonical URI of a base unit resource:

```text
systemd://system/unit/service/sshd
systemd://user/albe/unit/service/cortana
```

and returns the same compact unit representation exposed by reading that base Resource.

Fallback tools accept only canonical base Resource URIs so their addressing contract does not become more permissive than native Resource access.

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

### Deployment exposure

The fallback tools belong to the `resource_api_fallback` tool group defined by ADR 0012. That group is enabled by default.

It can be disabled with:

```yaml
tools:
  groups:
    resource_api_fallback: false
```

When disabled, the following overlapping tools are not exposed unless individually enabled:

```text
list_units
read_unit
read_unit_definition
```

The Resources themselves remain available through MCP.

`list_unit_types` does not belong to this group because it exposes mcp-systemd-specific semantic introspection rather than duplicating Resource protocol operations.

The fallback should be disabled only when the deployment harness gives the model an equivalent path to:

- discover concrete unit Resources;
- discover or otherwise address semantic sub-resources such as `/definition`;
- read those Resources.

A harness that only exposes `resources/list` and `resources/read` but does not make Resource Templates or the definition view discoverable is not yet equivalent for the current interface.

## Consequences

- mcp-systemd does not depend on a harness-specific Resource projection.
- Models can discover and read units even when the harness does not expose Resource operations directly.
- Harnesses with complete native Resource support can remove overlapping tools through one group flag.
- Individual fallback tools can still be enabled or disabled as deployment exceptions.
- The model never needs a generic `read_resource` abstraction.
