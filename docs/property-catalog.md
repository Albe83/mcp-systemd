# Unit property catalog

[`catalog/systemd-properties.yaml`](../catalog/systemd-properties.yaml) is the
standalone declarative catalog of public unit properties. It is separate from
the server's YAML configuration and contains no runtime values.

This first increment supplies data and documentation only. The server does not
load the catalog yet. Catalog installation/loading, property discovery and
reading through MCP are later increments; existing tools and resources are
unchanged. Modification capabilities are deferred.

## Format

The root contains `version: 1` and `interfaces`. Each full D-Bus interface name
maps native property names to descriptors:

```yaml
version: 1
interfaces:
  org.freedesktop.systemd1.Service:
    Restart:
      name: restart
      unit_types: [service]
      group: restart
      kind: configuration
      description: Policy for automatically restarting the service.
      dbus_signature: s
      schema:
        type: string
```

Every descriptor requires these fields:

| Field | Meaning |
| --- | --- |
| `name` | Public lower_snake_case name; matches `^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$` |
| `unit_types` | Non-empty list of unique supported unit types: `service`, `timer` |
| `group` | Discovery category: `metadata`, `execution`, `restart`, `security`, `scheduling` |
| `kind` | `metadata` or `configuration` in this seed |
| `description` | Short English explanation of the returned value |
| `dbus_signature` | Native D-Bus signature; internal binding metadata |
| `schema` | JSON Schema describing the exported value, using Draft 2020-12 vocabulary |

The interface and native property name identify the binding. Their names and
the D-Bus signature remain internal. The intended public identity is, for
example, `systemd://system/unit/service/sshd/property/restart`. This URI is not
implemented by the current server.

Public names must be unique across all descriptors applicable to the same unit
type. A generic Unit property cannot share a public name with a Service/Timer
property when their `unit_types` overlap. Duplicate YAML keys, unknown format
fields and ambiguous mappings are invalid; later loading must reject them rather
than silently overwrite an entry.

The catalog contains no writable flags, setters, persistence settings, defaults,
conversion expressions, templates or executable code. Adding a simple property
changes the catalog, not a Python mapping table.

## Initial coverage

The 14 bindings provide 8 applicable properties for services and 7 for timers:

| Interface | Public names |
| --- | --- |
| `org.freedesktop.systemd1.Unit` | `description` |
| `org.freedesktop.systemd1.Service` | `type`, `restart`, `restart_delay_usec`, `user`, `group`, `working_directory`, `no_new_privileges` |
| `org.freedesktop.systemd1.Timer` | `persistent`, `accuracy_usec`, `randomized_delay_usec`, `wake_system`, `on_clock_change`, `on_timezone_change` |

Values are those interpreted by the manager, including applied overrides and
defaults. This is an intentionally incomplete catalog, not a reconstruction of
the unit file or the complete execution environment of a running process.

Relations to other units are excluded from this catalog, including dependencies,
ordering and the timer's activated unit. Their representation will be designed
separately; this increment does not prescribe that future interface.

Empty user, group or working-directory settings are preserved. They do not
assert that the running process has an empty identity or directory. In
particular, the WorkingDirectory property may include systemd's special setting
notation; preserve it as reported, rather than claiming it is always an absolute
filesystem path. `persistent` concerns missed calendar events, not general
recovery of every monotonic timer schedule.

Command properties such as ExecStart, timer calendar/monotonic structs,
environment properties and resource limits are deferred. They require separate
decisions about compound values, runtime components and special-value semantics.

## Values and schemas

This seed requires only generic scalar conversion:

| D-Bus signature | JSON Schema |
| --- | --- |
| `s` | `type: string` |
| `b` | `type: boolean` |
| `t` | `type: integer`, range 0 through 18446744073709551615 |

Empty strings, false and zero remain values. There are no schema defaults
or string enums; new systemd versions may add service types or restart policies.

Durations retain their native microsecond units. Unsigned 64-bit values must
remain exact; consumers need lossless integer handling beyond the JavaScript
safe-integer range. Do not round values, convert durations to seconds, stringify
numbers or replace an integer sentinel with null. Special values such as
UINT64_MAX must be interpreted per property; a future friendly representation
requires a separate documented conversion decision.

The intended future read payload is:

```json
{
  "description": "Policy for automatically restarting the service.",
  "schema": {"type": "string"},
  "value": "on-failure"
}
```

This is an illustrative future contract, not output of an existing endpoint.
Schemas describe `value`, not the wrapper. Discovery can return descriptors
without retrieving their values; property reads must obtain fresh values.

## Missing and invalid data

| Situation | Intended behavior when the catalog is integrated |
| --- | --- |
| Native property has no mapping | Deliberately unmapped; do not expose it |
| Mapping exists but native interface/property is absent | Unavailable on this unit/manager; omit from its discovery |
| Reading an available mapped property fails | Report the read failure; never substitute null or a default |
| Catalog is malformed, ambiguous or has duplicate keys | Reject the catalog; this is not an availability gap |
| Returned signature/value conflicts with the descriptor | Report a contract mismatch; do not reinterpret it as missing |

Membership alone does not prove runtime availability. Availability must later
be checked against the actual manager. An incomplete catalog is valid and should
not prevent startup; invalid catalog structure is a separate error.

## Adding a property

1. Verify its interface, native name, signature, units and semantics against the
   target systemd documentation/source; inspect a real unit when available.
2. Add a descriptor under its native interface/property key. Choose a meaningful
   unique public name and applicable unit types.
3. Describe the value precisely, including empty/special-value behavior. Select
   a group/kind and supply a value schema. Do not promise modification support.
4. Check YAML duplicate keys, descriptor shape, names and uniqueness for
   overlapping unit types. Check schemas against the Draft 2020-12 meta-schema.
5. Compare with native properties when possible. Missing properties on other
   systemd versions are availability differences, not grounds for inventing data.

For generic conversion, add data only. A property needing new semantic
conversion (for example struct positions translated into named fields) requires
a separate design; do not embed executable conversion code in the catalog.

## Authoritative references

Native names/signatures in this seed were checked against systemd v257, matching
the version used in the initial D-Bus inspection:

- [Unit properties](https://github.com/systemd/systemd/blob/v257/src/core/dbus-unit.c)
- [Service properties](https://github.com/systemd/systemd/blob/v257/src/core/dbus-service.c)
- [Execution properties exported by services](https://github.com/systemd/systemd/blob/v257/src/core/dbus-execute.c)
- [Timer properties](https://github.com/systemd/systemd/blob/v257/src/core/dbus-timer.c)
- [D-Bus interface documentation](https://github.com/systemd/systemd/blob/v257/man/org.freedesktop.systemd1.xml)
- [Unit semantics](https://github.com/systemd/systemd/blob/v257/man/systemd.unit.xml)
- [Execution settings](https://github.com/systemd/systemd/blob/v257/man/systemd.exec.xml)
- [Timer semantics](https://github.com/systemd/systemd/blob/v257/man/systemd.timer.xml)
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)
