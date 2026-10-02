# ADR 0008: Use MCP tool annotations as behavioral metadata

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

MCP provides standard Tool Annotations that describe behavioral properties of tools. These annotations are visible to clients and can help them reason about how a tool behaves.

mcp-systemd should use these standard annotations rather than encoding the same facts in model-facing descriptions.

Tool exposure is a separate deployment concern. It is configured independently through tool groups and per-tool overrides as defined in ADR 0012.

## Decision

Every mcp-systemd tool must declare the applicable standard MCP Tool Annotations.

All current tools are explicitly declared as read-only and closed-world.

Tool descriptions remain focused on helping the model decide when to invoke the tool. Behavioral metadata belongs in MCP annotations.

Annotations describe the tool to MCP clients and models. They do not determine whether the tool is exposed by a deployment and are not used as configuration feature flags.

## General design principle

1. Prefer standard protocol metadata over duplicating behavioral facts in prose.
2. Keep model-facing descriptions focused on invocation decisions.
3. Treat annotations as descriptive semantics, not as exposure configuration or authorization.
4. Keep deployment exposure configuration independent from MCP annotations.

## Consequences

- Clients receive standard MCP behavioral metadata.
- Tool descriptions remain concise.
- Deployment configuration can evolve without redefining the meaning of MCP annotations.
- Tool annotations and tool exposure groups can change independently when they serve different purposes.
