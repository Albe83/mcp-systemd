# ADR 0002: Scope one MCP server instance to one host

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

A systemd unit is meaningful within a specific systemd manager running on a host. The MCP resource model could include a machine identifier in every resource URI, allowing one server to address multiple hosts, or it could make the host an execution boundary of the MCP server itself.

Including remote-host addressing in the initial resource model would add an orthogonal dimension before the unit model is established.

## Decision

Each mcp-systemd server instance represents exactly one host.

The host identity is therefore part of the MCP server context and is **not** encoded in systemd resource URIs.

Remote or multi-host orchestration is outside the initial resource model.

## Consequences

- Resource URIs remain compact and stable within a server instance.
- The MCP interface focuses on modeling systemd rather than remote execution.
- Multi-host administration can later be implemented by composing multiple MCP server instances or by introducing a separate orchestration layer.
- If multi-host support is ever added directly to mcp-systemd, it will require a new explicit architectural decision.
