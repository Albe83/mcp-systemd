# Semantic evaluation suite

This directory contains repeatable semantic evaluations for the MCP interface.

The goal is not only to verify that a model reaches a correct final answer. The suite also evaluates whether the MCP interface guides the model toward the right capability, arguments, resources, and amount of context.

## What to observe

For each case, capture:

1. tool calls and arguments;
2. resource discovery and reads;
3. unnecessary interactions;
4. final answer;
5. whether the model inferred unsupported capabilities.

The expected trace is intentionally not always unique. A case can define:

- `required`: behavior that must occur;
- `acceptable`: behavior that is not necessary but is still valid;
- `forbidden`: behavior that indicates semantic confusion, wasted context, or invented capability.

Semantic interactions are intentionally harness-agnostic:

- `kind: unit_discovery` means the model must cause discovery of the relevant unit Resources. This may be realized through `list_units`, native `resources/list`, or an equivalent harness projection.
- `kind: resource` means the model must cause that Resource view to be read. This may be realized through native MCP Resource access or through mcp-systemd semantic fallback tools such as `read_unit` and `read_unit_definition`.
- `kind: tool` is used only when the specific tool choice itself is part of the semantic expectation.

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
      interactions: []
      answer:
        semantics: []

    notes: |
      Human explanation of what the case is testing.
```

A concrete tool expectation:

```yaml
- kind: tool
  name: list_unit_types
```

Semantic unit discovery:

```yaml
- kind: unit_discovery
  type: service
  user: testuser
```

A Resource read:

```yaml
- kind: resource
  uri: systemd://system/unit/service/sshd
```

## Validate the suite

Validate case structure and duplicate IDs before running evaluations:

```bash
uv run python evals/validate.py
```

The validator checks structure only. Semantic expectations are intentionally reviewed against the observed model trace and answer.

## Execution protocol

Run the same cases against the same server fixture when comparing models or interface revisions.

Do not add instructions to the model that reveal the expected MCP path. Submit only the case `prompt` plus the normal harness/system instructions.

Record the model, harness, server revision, fallback configuration, observed interactions, and result using `result-template.yaml`.

The suite is expected to evolve with the interface. Any new model-facing capability should add or update semantic eval cases that demonstrate when it should be used, when it should not be used, and what decision it enables.
