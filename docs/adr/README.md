# Architecture Decision Records

This directory contains the Architecture Decision Records (ADRs) for **mcp-systemd**.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-layered-mcp-interface.md) | Layer the interface into resources, primitives, and intent workflows | Accepted |
| [0002](0002-single-host-server-boundary.md) | Scope one MCP server instance to one host | Accepted |
| [0003](0003-systemd-unit-resource-uris.md) | Use scoped semantic URIs for systemd unit resources | Accepted |
| [0004](0004-interface-first-iterative-development.md) | Develop interface-first using TDD and a simulated systemd backend | Accepted |
| [0005](0005-security-by-default.md) | Apply security-by-default to network exposure | Accepted |
| [0006](0006-resource-discovery.md) | Discover loaded systemd units through resources/list | Accepted |
| [0007](0007-model-controlled-resource-discovery.md) | Provide model-controlled discovery for resource-oriented interfaces | Accepted |
| [0008](0008-tool-annotations.md) | Use MCP tool annotations as behavioral metadata | Accepted |
| [0009](0009-model-facing-token-discipline.md) | Optimize model-facing interfaces for decision value and token efficiency | Accepted |
| [0010](0010-unit-state-and-subresources.md) | Keep core unit state on the base resource and optional heavy views as sub-resources | Accepted |
| [0011](0011-semantic-resource-api-fallback.md) | Provide semantic Resource API fallback tools | Accepted |
| [0012](0012-tool-exposure-groups.md) | Configure tool exposure with groups and per-tool overrides | Accepted |
| [0013](0013-hexagonal-systemd-boundary.md) | Separate the MCP interface from systemd backends with a hexagonal boundary | Accepted |
| [0014](0014-configurable-systemd-backend.md) | Select the systemd backend from configuration | Accepted |
