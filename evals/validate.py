from pathlib import Path
import sys

import yaml


CASES_DIR = Path(__file__).parent / "cases"
CATEGORIES = {"discovery", "state", "definition", "negative"}
INTERACTION_KINDS = {"tool", "resource", "unit_discovery"}


def fail(message: str) -> None:
    raise ValueError(message)


def require_list(value: object, label: str, case_id: str) -> list:
    if not isinstance(value, list):
        fail(f"{case_id}: {label} must be a list")
    return value


def validate_interaction(interaction: object, case_id: str) -> None:
    if not isinstance(interaction, dict):
        fail(f"{case_id}: interaction must be an object")

    kind = interaction.get("kind")
    if kind not in INTERACTION_KINDS:
        fail(f"{case_id}: invalid interaction kind {kind!r}")

    if kind == "tool":
        if not isinstance(interaction.get("name"), str) or not interaction["name"]:
            fail(f"{case_id}: tool interaction requires name")
        arguments = interaction.get("arguments", {})
        if not isinstance(arguments, dict):
            fail(f"{case_id}: tool arguments must be an object")

    if kind == "resource":
        if not isinstance(interaction.get("uri"), str) or not interaction["uri"]:
            fail(f"{case_id}: resource interaction requires uri")

    if kind == "unit_discovery":
        unit_type = interaction.get("type")
        user = interaction.get("user")
        if unit_type is not None and (
            not isinstance(unit_type, str) or not unit_type
        ):
            fail(f"{case_id}: unit discovery type must be a non-empty string")
        if user is not None and (not isinstance(user, str) or not user):
            fail(f"{case_id}: unit discovery user must be a non-empty string")


def validate_semantics(value: object, label: str, case_id: str) -> None:
    semantics = require_list(value, label, case_id)
    if not all(isinstance(item, str) and item for item in semantics):
        fail(f"{case_id}: {label} entries must be non-empty strings")


def validate_case(case: dict, seen_ids: set[str]) -> None:
    case_id = case.get("id")
    if not isinstance(case_id, str) or not case_id:
        fail("case requires a non-empty id")
    if case_id in seen_ids:
        fail(f"duplicate case id: {case_id}")
    seen_ids.add(case_id)

    if case.get("category") not in CATEGORIES:
        fail(f"{case_id}: invalid category")

    tags = case.get("tags", [])
    if not isinstance(tags, list) or not all(
        isinstance(tag, str) and tag for tag in tags
    ):
        fail(f"{case_id}: tags must be a list of non-empty strings")

    if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
        fail(f"{case_id}: prompt must be non-empty")

    expected = case.get("expected", {})
    forbidden = case.get("forbidden", {})
    if not isinstance(expected, dict):
        fail(f"{case_id}: expected must be an object")
    if not isinstance(forbidden, dict):
        fail(f"{case_id}: forbidden must be an object")

    for interaction in require_list(
        expected.get("required", []), "expected.required", case_id
    ):
        validate_interaction(interaction, case_id)

    for interaction in require_list(
        expected.get("acceptable", []), "expected.acceptable", case_id
    ):
        validate_interaction(interaction, case_id)

    for interaction in require_list(
        forbidden.get("interactions", []), "forbidden.interactions", case_id
    ):
        validate_interaction(interaction, case_id)

    expected_answer = expected.get("answer", {})
    forbidden_answer = forbidden.get("answer", {})
    if not isinstance(expected_answer, dict):
        fail(f"{case_id}: expected.answer must be an object")
    if not isinstance(forbidden_answer, dict):
        fail(f"{case_id}: forbidden.answer must be an object")

    validate_semantics(
        expected_answer.get("semantics", []),
        "expected.answer.semantics",
        case_id,
    )
    validate_semantics(
        forbidden_answer.get("semantics", []),
        "forbidden.answer.semantics",
        case_id,
    )


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
