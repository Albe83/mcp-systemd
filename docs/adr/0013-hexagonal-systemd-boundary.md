# ADR 0013: Separate the MCP interface from systemd backends with a hexagonal boundary

- **Status:** Accepted
- **Date:** 2026-10-03

## Context

The initial mock implementation stored unit fixtures, lookup logic, MCP URI construction, MCP serialization, and FastMCP Resource generation close together.

That was useful for quickly validating the first interface slice, but it coupled the simulated data source to the MCP adapter. Replacing the mock with a real systemd implementation would therefore require changes across the interface layer.

The simulated backend must remain useful for safe development and semantic evaluation, while the MCP server itself should be the same implementation used with a production backend.

## Decision

mcp-systemd adopts a small hexagonal boundary.

### Domain

`src/mcp_systemd/domain/` contains the systemd-facing data model and the outbound port:

```text
domain/
├── systemd.py
├── unit.py
├── unit_service.py
└── unit_timer.py
```

The domain model contains no MCP URI, serialization, FastMCP, D-Bus, CLI, or mock concepts.

`Systemd` is the port consumed by the MCP application. It initially provides:

```text
list_units(...)
get_unit(ref)
get_unit_definition(ref)
```

Additional unit-type models are added to `domain/` as they become necessary.

### Backends

`src/mcp_systemd/backends/` contains concrete implementations of the `Systemd` port.

The first implementation is:

```text
MockSystemd
```

It is an in-memory adapter used for development, functional testing, and semantic evaluation.

A future production adapter can use D-Bus or another appropriate systemd mechanism without changing the MCP Resources or Tools.

### MCP adapter

MCP-specific identity and representation remain outside the domain.

In particular:

```text
UnitRef <-> systemd://... URI
Unit    -> Resource/tool payload
```

are adapter responsibilities.

The FastMCP `UnitResourceProvider` is also an MCP adapter. It depends on the domain `Systemd` port and must not contain mock-specific behavior.

Concrete Resources created during discovery capture only a `UnitRef`. Reading a Resource performs a fresh `get_unit(ref)` call so runtime state is not frozen at discovery time.

### Composition

`server.py` is the composition root.

During the current development phase:

```text
FastMCP
  -> Resources / Tools
  -> Systemd port
  -> MockSystemd
```

The backend is injectable. A future production composition replaces only the final adapter.

## Consequences

- The mock is a replaceable backend, not part of the MCP object model.
- The domain has no dependency on FastMCP or MCP representation details.
- Resources and Tools share the same backend contract.
- Resource reads can reflect state changes that occur after discovery.
- Semantic tests exercise the same MCP implementation intended for production.
- New backend implementations can be introduced without changing the model-facing interface.
