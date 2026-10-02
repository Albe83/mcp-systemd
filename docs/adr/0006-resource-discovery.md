# ADR 0006: Discover loaded systemd units through resources/list

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

Resource templates describe which systemd unit resources can be addressed, but clients also need a lightweight way to discover concrete resources currently known by systemd.

Systemd distinguishes units currently loaded by a manager from unit files installed on disk. The initial MCP discovery model should remain narrow and map to manager runtime views rather than attempt to enumerate every installed unit file.

## Decision

For each systemd manager represented by mcp-systemd, unit discovery has the logical semantics of:

```text
systemctl list-units --all
```

restricted to the unit types currently supported by mcp-systemd.

Initially those types are:

```text
service
timer
```

`resources/list` exposes the union of the concrete unit Resources known across the represented managers on the host. Therefore a single Resource catalog may contain both system-manager and user-manager units.

Discovery includes inactive loaded units and does not attempt to mirror `systemctl list-unit-files`.

Each concrete resource exposed through `resources/list` carries lightweight MCP metadata:

```json
{
  "uri": "systemd://system/unit/service/sshd",
  "name": "sshd",
  "description": "OpenSSH server daemon"
}
```

Reading the base unit resource returns its compact current representation:

```json
{
  "description": "OpenSSH server daemon",
  "load_state": "loaded",
  "active_state": "active",
  "sub_state": "running"
}
```

The unit name is deliberately not repeated in the resource payload. The URI already identifies the resource, including manager scope, unit type, and semantic unit name. Repeating identity fields in the content would consume model context without adding information.

This establishes a general separation:

```text
URI
    -> resource identity

resource metadata
    -> discovery hints

resource content
    -> properties of the identified resource
```

Runtime state and the use of optional sub-resources for larger views are defined in ADR 0010.

## Consequences

- Resource discovery has a clear per-manager systemd analogue without exposing every installed unit file.
- `resources/list` can represent more than one systemd manager while preserving manager scope in each URI.
- `resources/list` remains lightweight and suitable for catalog/discovery use.
- Resource content does not duplicate identity already encoded in the URI.
- The base resource provides compact state useful for common operational decisions.
- Discovery of which user managers are represented is an implementation concern that can be refined later without changing the URI or resource-content contract.
