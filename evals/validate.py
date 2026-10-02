from pathlib import Path
import sys

import yaml


CASES_DIR = Path(__file__).parent / "cases"
CATEGORIES = {"discovery", "state", "definition", "negative"}
CALL_KINDS = {"tool", "resource"}


def fail(message: str) -> None:
    raise ValueError(message)


def validate_call(call: dict, case_id: str) -> None:
    kind = call.get("kind")
    if kind not in CALL_KINDS:
        fail(f"{case_id}: invalid call kind {kind!r}")

    if kind == "tool" and not call.get("name"):
        fail(f"{case_id}: tool call requires name")

    if kind == "resource" and not call.get("uri"):
        fail(f"{case_id}: resource call requires uri")


def validate_case(case: dict, seen_ids: set[str]) -> None:
    case_id = case.get("id")
    if not isinstance(case_id, str) or not case_id:
        fail("case requires a non-empty id")
    if case_id in seen_ids:
        fail(f"duplicate case id: {case_id}")
    seen_ids.add(case_id)

    if case.get("category") not in CATEGORIES:
        fail(f"{case_id}: invalid category")

    if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
        fail(f"{case_id}: prompt must be non-empty")

    expected = case.get("expected", {})
    forbidden = case.get("forbidden", {})

    for call in expected.get("required", []):
        validate_call(call, case_id)
    for call in expected.get("acceptable", []):
        validate_call(call, case_id)
    for call in forbidden.get("calls", []):
        validate_call(call, case_id)


def main() -> int:
    seen_ids: set[str] = set()
    files = sorted(CASES_DIR.glob("*.yaml"))

    if not files:
        fail("no semantic eval case files found")

    count = 0
    for path in files:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        cases = data.get("cases") if isinstance(data, dict) else None
        if not isinstance(cases, list):
            fail(f"{path}: top-level 'cases' must be a list")

        for case in cases:
            if not isinstance(case, dict):
                fail(f"{path}: each case must be an object")
            validate_case(case, seen_ids)
            count += 1

    print(f"validated {count} semantic eval cases")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as error:
        print(f"semantic eval validation failed: {error}", file=sys.stderr)
        sys.exit(1)
