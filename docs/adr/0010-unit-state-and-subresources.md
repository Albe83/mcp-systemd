# ADR 0010: Keep core unit state on the base resource and optional heavy views as sub-resources

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

Once a model has discovered a systemd unit, the next useful operation is usually to inspect its current state.

Not every view of a unit has the same value or token cost. Runtime state is compact, broadly useful, and frequently needed. Unit-file content can be much larger, may include drop-ins, and is only useful for configuration-oriented questions.

Putting all available information in the base unit resource would waste model context. Moving every concern into sub-resources would instead force extra reads for information that is almost always needed.

## Decision

The base unit resource represents the compact current state of the unit.

For example:

```text
systemd://system/unit/service/sshd
```

returns:

```json
{
  "description": "OpenSSH server daemon",
  "load_state": "loaded",
  "active_state": "active",
  "sub_state": "running"
}
```

The base payload contains the generic systemd unit state shared across unit types:

- `load_state`;
- `active_state`;
- `sub_state`.

Type-specific details are not added yet.

The unit definition is exposed separately:

```text
systemd://system/unit/{type}/{name}/definition
systemd://user/{user}/unit/{type}/{name}/definition
```

The `definition` sub-resource is text and represents the unit file together with its drop-ins, with semantics equivalent to the information exposed by `systemctl cat`.

The URI uses `definition` rather than `content` or `contents` because it names the semantic view instead of the implementation or storage representation.

`resources/list` continues to enumerate base unit resources only. Definition sub-resources are addressable through their resource templates and do not expand the normal discovery catalog.

## Sub-resource criterion

Prefer a field on the base resource when the information is:

- compact;
- broadly useful;
- commonly needed for the next model decision;
- part of the core representation of the object.

Prefer a sub-resource when the information is:

- a semantically distinct view;
- potentially large or expensive in tokens;
- needed only for specific tasks;
- useful independently from the common object representation.

This criterion intentionally optimizes both semantic clarity and model context usage.

## Consequences

- Reading a unit resource provides enough state for common operational reasoning without a second read.
- The base resource remains small and type-agnostic.
- Large unit definitions consume tokens only when explicitly requested.
- New expensive or specialized views can follow the same sub-resource pattern when justified.
- Sub-resources are not created merely to mirror backend commands or implementation boundaries.
