from urllib.parse import urlparse

from mcp_systemd.domain.unit import Unit, UnitRef


def unit_uri(ref: UnitRef) -> str:
    if ref.scope == "system":
        return f"systemd://system/unit/{ref.type}/{ref.name}"

    return f"systemd://user/{ref.user}/unit/{ref.type}/{ref.name}"


def parse_unit_uri(uri: str) -> UnitRef:
    parsed = urlparse(uri)
    if parsed.scheme != "systemd":
        raise ValueError("Invalid unit resource URI")

    parts = [part for part in parsed.path.split("/") if part]

    if parsed.netloc == "system" and len(parts) == 3 and parts[0] == "unit":
        _, unit_type, name = parts
        ref = UnitRef(
            scope="system",
            type=unit_type,
            name=name,
        )
    elif (
        parsed.netloc == "user"
        and len(parts) == 4
        and parts[1] == "unit"
    ):
        user, _, unit_type, name = parts
        ref = UnitRef(
            scope="user",
            user=user,
            type=unit_type,
            name=name,
        )
    else:
        raise ValueError("Invalid unit resource URI")

    if unit_uri(ref) != uri:
        raise ValueError("Unit resource URI must be canonical")

    return ref


def unit_content(unit: Unit) -> dict[str, str]:
    return {
        "description": unit.description,
        "load_state": unit.load_state,
        "active_state": unit.active_state,
        "sub_state": unit.sub_state,
    }


def unit_discovery(unit: Unit) -> dict[str, str]:
    return {
        "uri": unit_uri(unit.ref),
        "name": unit.ref.name,
        "description": unit.description,
    }
