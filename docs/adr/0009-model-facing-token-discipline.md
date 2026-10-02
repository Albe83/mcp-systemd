# ADR 0009: Optimize model-facing interfaces for decision value and token efficiency

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

Everything exposed to a model consumes context.

Tool names, descriptions, parameter schemas, enum values, resource descriptions, tool results, and error messages all compete for a limited token budget. This cost is not only economic: some models may have limited context capacity or limited hardware resources for processing large prompts.

Model-facing metadata therefore has two responsibilities:

1. help the model make the right decision;
2. do so with the minimum semantic payload necessary.

Documentation written for developers is not automatically appropriate for models. Implementation details, architectural rationale, protocol plumbing, reassurance, and redundant explanation consume context without necessarily improving tool selection or execution.

A tool description should also help the model avoid unnecessary calls by making the intended invocation boundary clear.

## Decision

Treat model context as a scarce architectural resource.

Every model-facing token must contribute materially to one of the following:

- deciding whether to use a capability;
- deciding which capability to use;
- supplying valid arguments;
- interpreting a result;
- avoiding an incorrect or unnecessary action.

If information does not materially improve one of these decisions, it should not be exposed to the model.

### Names and descriptions

Tool and resource names should carry as much semantic meaning as practical.

Descriptions should:

- state what the capability provides;
- subtly indicate when it is useful when that distinction helps tool selection;
- make the non-use case inferable where practical;
- avoid developer-oriented explanation;
- avoid repeating information already expressed by the name, schema, annotations, or protocol;
- use the shortest wording that preserves the necessary decision signal.

For example, a discovery tool may say that it is useful when the exact object name is unknown. This both suggests when to invoke it and implies that it is unnecessary when the object is already known.

### Prefer structured semantics over prose

When information can be represented by MCP or schema primitives, prefer the structured representation.

Examples include:

- behavioral properties in Tool Annotations;
- accepted values in schemas or enums;
- required and optional arguments in the input schema;
- typed result structures instead of explanatory prose.

Do not duplicate the same semantic fact in a description unless the duplication materially improves model decision-making.

A useful separation is:

```text
Protocol / schema / annotations
    -> machine-readable semantics

Name / description
    -> model decision guidance

ADR / developer documentation
    -> implementation rationale and architecture
```

### Token cost includes the whole tool lifecycle

Tool design must consider at least three token costs:

```text
definition cost
    name + description + input schema

call cost
    model-generated arguments

result cost
    tool output returned to the model
```

A small improvement repeated across many tools can materially reduce steady-state context usage.

Tool results should therefore also be designed for semantic density. Return only information needed for the likely next decision, and avoid verbose wrappers or duplicated fields without demonstrated value.

### Minimize the exposed surface

Do not expose a capability merely because it exists in the underlying system.

Each additional tool increases:

- context consumption;
- tool-selection ambiguity;
- the model's search space;
- the chance of an unnecessary or incorrect call.

Prefer the smallest useful set of high-signal capabilities.

## General design principle

**Everything exposed to the model must earn its tokens.**

Before adding model-facing information, ask:

1. Can this information change a model decision?
2. Is it already expressed structurally elsewhere?
3. Can the same decision signal be expressed with fewer tokens?
4. Does it help the model know when to use the capability?
5. Does it also help the model infer when not to use it?
6. Is the returned information necessary for the next likely decision?

If the answer does not justify the context cost, omit it.

## Consequences

- Model-facing interfaces are optimized for decisions rather than human documentation.
- Tool definitions remain compact as the server grows.
- Tool selection becomes less ambiguous.
- Unnecessary tool calls are discouraged by the interface itself.
- Result payloads are expected to remain intentionally small.
- Protocol metadata and schemas carry semantics that would otherwise consume prose tokens.
- Context efficiency becomes an explicit review criterion for future tools and resources.
