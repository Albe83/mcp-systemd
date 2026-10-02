# Semantic evaluation suite

This directory contains repeatable semantic evaluations for the MCP interface.

The goal is not only to verify that a model reaches a correct final answer. The suite also evaluates whether the MCP interface guides the model toward the right capability, arguments, resources, and amount of context.

## What to observe

For each case, capture:

1. tool calls and arguments;
2. resource reads;
3. unnecessary calls or reads;
4. final answer;
5. whether the model inferred unsupported capabilities.

The expected trace is intentionally not always unique. A case can define:

- `required`: behavior that must occur;
- `acceptable`: behavior that is not necessary but is still valid;
- `forbidden`: behavior that indicates semantic confusion, wasted context, or invented capability.

## Rating

Use one overall rating per case:

- `pass`: required behavior is satisfied, no forbidden behavior occurs, and the final answer is semantically correct;
- `acceptable`: the answer is correct and no forbidden behavior occurs, but the path includes avoidable work;
- `fail`: required behavior is missing, forbidden behavior occurs, or the answer is semantically wrong.

Keep notes when a case is rated `acceptable` or `fail`.

## Case format

```yaml
cases:
  - id: unique-case-id
    category: discovery | state | definition | negative
    tags: []

    prompt: |
      User-like prompt.

    expected:
      required: []
      acceptable: []
      answer:
        semantics: []

    forbidden:
      calls: []
      answer:
        semantics: []

    notes: |
      Human explanation of what the case is testing.
```

A call can be a tool call:

```yaml
- kind: tool
  name: list_units
  arguments:
    type: service
```

or a resource read:

```yaml
- kind: resource
  uri: systemd://system/unit/service/sshd
```

## Execution protocol

Run the same cases against the same server fixture when comparing models or interface revisions.

Do not add instructions to the model that reveal the expected MCP path. Submit only the case `prompt` plus the normal harness/system instructions.

Record the model, harness, server revision, and result using `result-template.yaml`.

The suite is expected to evolve with the interface. Any new model-facing capability should add or update semantic eval cases that demonstrate when it should be used, when it should not be used, and what decision it enables.
