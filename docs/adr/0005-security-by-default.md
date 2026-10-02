# ADR 0005: Apply security-by-default to network exposure

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

mcp-systemd is intended to expose operations over systemd. As the project evolves, those operations may be able to control privileged system services and therefore represent a sensitive administrative interface.

Using HTTP as the default transport is desirable, but listening on all interfaces would expose the server to the network by default.

## Decision

mcp-systemd follows a **security-by-default** principle for network exposure.

The default HTTP listener is:

```text
127.0.0.1:48000
```

Specifically:

- the server binds to the loopback interface by default;
- it does not listen on external network interfaces unless explicitly configured to do so;
- a high, non-common port (`48000`) is used as the project default;
- host and port may be overridden explicitly through the YAML configuration;
- broader network exposure must be an explicit operator decision.

## Consequences

- A default installation is reachable only from the local host.
- Remote access requires deliberate configuration rather than happening accidentally.
- Binding to loopback reduces exposure but is not a substitute for authentication, authorization, or transport security if remote access is introduced later.
