# ADR 0003: Use scoped semantic URIs for systemd unit resources

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

Systemd units can belong to the system manager or to a per-user manager. The same logical unit name may therefore identify different objects depending on its scope.

The first resource types to be modeled are services and timers, because they represent the most common initial use cases.

Systemd conventionally includes the unit type in the unit name, for example `httpd.service`. In the MCP resource model, however, the type is represented structurally in the URI. Repeating the suffix would be redundant and less aligned with how users normally refer to units.

## Decision

The unit resource templates are:

```text
systemd://system/unit/{type}/{name}
systemd://user/{user}/unit/{type}/{name}
```

The rules are:

- `system` and `user` identify the systemd manager scope.
- User-scoped resources include the user identity because each user has a distinct systemd user manager.
- `{type}` identifies the systemd unit type.
- The initial supported values for `{type}` are `service` and `timer`.
- `{name}` does **not** include the systemd unit suffix.
- The server maps the semantic URI to the canonical systemd unit name internally.

Examples:

```text
systemd://system/unit/service/httpd
systemd://system/unit/timer/dnf-makecache
systemd://user/albe/unit/service/cortana
systemd://user/albe/unit/timer/backup
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
systemd://system/unit/service/foo@bar
```

maps to:

```text
foo@bar.service
```

## Consequences

- Manager scope is explicit and unambiguous in every unit resource URI.
- Unit type is a parameter of the resource model rather than being hardcoded into separate templates.
- The resource identifier remains semantic rather than mirroring systemd filename syntax.
- Models can use names closer to typical user language, such as `httpd` instead of `httpd.service`.
- The server must perform strict normalization between MCP resource identifiers and canonical systemd unit names.
- Additional unit types can be supported later without adding new resource templates.
