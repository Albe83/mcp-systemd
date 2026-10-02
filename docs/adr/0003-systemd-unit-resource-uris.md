# ADR 0003: Use scoped semantic URIs for systemd unit resources

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

Systemd units can belong to the system manager or to a per-user manager. The same logical unit name may therefore identify different objects depending on its scope.

The first resource types to be modeled are services and timers, because they represent the most common initial use cases.

Systemd conventionally includes the unit type in the unit name, for example `httpd.service`. In the MCP resource model, however, the type is already represented structurally in the URI. Repeating the suffix would be redundant and less aligned with how users normally refer to services and timers.

## Decision

The initial resource templates are:

```text
systemd://unit/system/service/{name}
systemd://unit/system/timer/{name}

systemd://unit/user/{user}/service/{name}
systemd://unit/user/{user}/timer/{name}
```

The rules are:

- `system` and `user` are distinct resource namespaces.
- User-scoped resources include the user identity because each user has a distinct systemd user manager.
- The initial supported unit types are `service` and `timer`.
- `{name}` does **not** include the systemd unit suffix.
- The server maps the semantic URI to the canonical systemd unit name internally.

Examples:

```text
systemd://unit/system/service/httpd
systemd://unit/system/timer/dnf-makecache
systemd://unit/user/albe/service/cortana
systemd://unit/user/albe/timer/backup
```

These correspond internally to unit names such as:

```text
httpd.service
dnf-makecache.timer
cortana.service
backup.timer
```

The same rule applies to instantiated units. For example:

```text
systemd://unit/system/service/foo@bar
```

maps to:

```text
foo@bar.service
```

## Consequences

- Scope is explicit and unambiguous in every unit resource URI.
- The resource identifier remains semantic rather than mirroring systemd filename syntax.
- Models can use names closer to typical user language, such as `httpd` instead of `httpd.service`.
- The server must perform strict normalization between MCP resource identifiers and canonical systemd unit names.
- Additional unit types can be added later without changing the URI structure.
