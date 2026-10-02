# ADR 0008: Use MCP tool annotations as behavioral metadata

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

MCP provides standard Tool Annotations that describe behavioral properties of tools. These annotations are visible to clients and can help them reason about how a tool behaves.

mcp-systemd will use these standard annotations rather than encoding the same facts in model-facing descriptions.

The server configuration should also be able to use behavioral classes to decide which tools are exposed by a particular deployment.

## Decision

Every mcp-systemd tool must declare the applicable standard MCP Tool Annotations.

The current discovery tools are explicitly declared as read-only and closed-world.

Tool descriptions remain focused on helping the model decide when to invoke the tool. Behavioral metadata belongs in MCP annotations.

Annotations are descriptive metadata, not an authorization boundary. Deployment policy remains a server-side concern.

The configuration surface will be extended so that deployments can exclude behavioral classes of tools before they are exposed through MCP. The default policy will remain conservative: read-only, closed-world tools are available; broader capabilities require explicit configuration.

## General design principle

1. Prefer standard protocol metadata over duplicating behavioral facts in prose.
2. Keep model-facing descriptions focused on invocation decisions.
3. Treat annotations as semantic metadata, not as security enforcement.
4. Apply deployment policy server-side before tools are exposed.
5. Default to the least powerful useful tool surface.

## Consequences

- Clients receive standard MCP behavioral metadata.
- Tool descriptions remain concise.
- Deployment policy can later be derived from the same behavioral classification without creating a parallel taxonomy.
- New operational tools must be classified explicitly.
