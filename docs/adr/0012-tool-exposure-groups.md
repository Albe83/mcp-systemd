# ADR 0012: Configure tool exposure with groups and per-tool overrides

- **Status:** Accepted
- **Date:** 2026-10-03

## Context

Different deployments need different model-facing tool surfaces.

Some differences are naturally expressed as feature-like switches. For example, the semantic Resource API fallback is useful for harnesses that do not expose MCP Resources directly to the model, but redundant for harnesses that already provide equivalent access.

Deployments may also need to expose or hide one specific tool without changing the rest of a group.

MCP Tool Annotations solve a different problem: they describe tool behavior to clients and models. They must not be reused as deployment feature flags.

## Decision

Each tool may belong to zero or more named exposure groups.

Groups are simple deployment feature flags. Their names and defaults are introduced incrementally as the interface evolves.

The configuration surface is:

```yaml
tools:
  groups:
    resource_api_fallback: true

  enable: []
  disable: []
```

The exposure decision is:

1. a tool listed in `disable` is hidden;
2. a tool listed in `enable` is exposed;
3. otherwise, a tool with no groups is exposed;
4. otherwise, all groups the tool belongs to must be enabled.

A tool may not be present in both `enable` and `disable`.

Unknown group names and unknown tool names are configuration errors so spelling mistakes do not silently change the exposed surface.

Tool groups are independent from MCP Tool Annotations. A group may exist for compatibility, maturity, functionality, or any other deployment reason.

The first group is:

```text
resource_api_fallback
```

with these members:

```text
list_units
read_unit
read_unit_definition
```

It is enabled by default.

## Consequences

- Deployments can switch coherent sets of tools on or off with a single flag.
- A deployment can make a precise exception with a per-tool override.
- Tools can participate in multiple independent feature flags.
- Tools that do not need grouping remain exposed by default.
- Exposure configuration remains independent from MCP behavioral metadata.
- New groups are added only when an actual deployment need appears.
