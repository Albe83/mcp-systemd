# ADR 0006: Discover loaded systemd units through resources/list

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

Resource templates describe which systemd unit resources can be addressed, but clients also need a lightweight way to discover concrete resources currently known by systemd.

Systemd distinguishes units currently loaded by a manager from unit files installed on disk. The initial MCP discovery model should remain narrow and map to the manager's current view rather than attempt to enumerate every installed unit file.

## Decision

`resources/list` is the logical equivalent of:

```text
systemctl list-units --all
```

restricted to the unit types currently supported by mcp-systemd.

Initially those types are:

```text
service
timer
```

Therefore discovery represents units currently known/loaded by the relevant systemd manager, including inactive loaded units, and does not attempt to mirror `systemctl list-unit-files`.

Each concrete resource exposed through `resources/list` carries lightweight MCP metadata:

```json
{
  "uri": "systemd://system/unit/service/sshd",
  "name": "sshd",
  "description": "OpenSSH server daemon"
}
```

For the initial interface, reading a unit resource returns only:

```json
{
  "name": "sshd",
  "description": "OpenSSH server daemon"
}
```

The resource payload will be expanded incrementally as the interface is designed and validated.

## Consequences

- Resource discovery has a clear systemd analogue without exposing every installed unit file.
- `resources/list` remains lightweight and suitable for catalog/discovery use.
- Resource content starts deliberately small and can evolve based on observed model needs.
- Discovery of user managers is an implementation concern that can be refined later without changing the URI or resource-content contract.
