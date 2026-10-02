# Contributing

Contributions are welcome. Keep changes small, focused, and easy to review.

## Workflow

1. Create a branch from `main`.
2. Make one logical change at a time.
3. Keep commits focused and self-contained.
4. Push the branch and open a pull request against `main`.
5. Update the branch if `main` has moved significantly.
6. Address review feedback with additional commits or by amending the existing ones when appropriate.
7. Merge only after the pull request is ready and checks are passing.

Prefer short-lived branches and small pull requests over large batches of unrelated changes.

Suggested branch prefixes:

```text
feat/
fix/
docs/
refactor/
test/
chore/
```

Examples:

```text
feat/service-resources
fix/user-scope-resolution
docs/resource-model
```

## Dependencies

Dependencies are resolved in `uv.lock`.

Use the locked environment for normal development:

```bash
uv sync --locked
```

When `pyproject.toml` dependencies change, regenerate and commit the lockfile:

```bash
uv lock
```

## Checks

Before opening or merging a pull request, run:

```bash
uv sync --locked
uv run python -m unittest discover -s tests
uv run python evals/validate.py
```

Functional tests protect code-level contracts. Semantic evals remain a separate model-facing corpus and are not replaced by functional tests.

The GitHub Actions `CI` workflow runs the same checks in a clean environment, but it is intentionally **manual only**. It does not run on pushes or pull requests. Trigger it from **Actions → CI → Run workflow** when remote verification is useful.

## Commit messages

Use a Conventional Commits style:

```text
<type>: <short description>
```

or, when a scope adds useful context:

```text
<type>(<scope>): <short description>
```

Common types:

- `feat`: new functionality
- `fix`: bug fix
- `docs`: documentation only
- `refactor`: internal change without changing behavior
- `test`: tests
- `chore`: maintenance or tooling

Examples:

```text
feat(resources): add generic unit resource template
fix(http): bind server to loopback by default
docs: document contribution workflow
refactor(server): simplify mock unit creation
```

Commit subjects should:

- be written in the imperative mood;
- start with a lowercase letter;
- not end with a period;
- stay concise and describe one logical change.

When additional context is useful, add a body after a blank line:

```text
fix(resources): reject unsupported unit types

Keep the public resource template generic while limiting the
initial mock implementation to service and timer units.
```

Use the body to explain **why** the change is needed or any important trade-off. Avoid repeating the diff.

If a commit relates to an issue, reference it in the footer when useful:

```text
Refs #12
Closes #12
```
