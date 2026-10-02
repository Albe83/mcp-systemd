from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

Scope = Literal["system", "user"]


@dataclass(frozen=True)
class UnitTypeRecord:
    name: str
    description: str


UNIT_TYPES = (
    UnitTypeRecord(
        name="service",
        description=(
            "A unit that represents and controls a service or process managed by systemd."
        ),
    ),
    UnitTypeRecord(
        name="timer",
        description=(
            "A unit that schedules time-based activation of another systemd unit."
        ),
    ),
)

SUPPORTED_TYPES = {unit_type.name for unit_type in UNIT_TYPES}


@dataclass(frozen=True)
class UnitRecord:
    scope: Scope
    type: str
    name: str
    description: str
    load_state: str
    active_state: str
    sub_state: str
    definition: str
    user: str | None = None

    @property
    def uri(self) -> str:
        if self.scope == "system":
            return f"systemd://system/unit/{self.type}/{self.name}"

        if self.user is None:
            raise ValueError("user-scoped units require a user")

        return f"systemd://user/{self.user}/unit/{self.type}/{self.name}"

    def content(self) -> dict[str, str]:
        return {
            "description": self.description,
            "load_state": self.load_state,
            "active_state": self.active_state,
            "sub_state": self.sub_state,
        }

    def discovery(self) -> dict[str, str]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
        }


MOCK_UNITS = (
    UnitRecord(
        scope="system",
        type="service",
        name="sshd",
        description="OpenSSH server daemon",
        load_state="loaded",
        active_state="active",
        sub_state="running",
        definition="""[Unit]
Description=OpenSSH server daemon

[Service]
ExecStart=/usr/sbin/sshd -D
""",
    ),
    UnitRecord(
        scope="system",
        type="service",
        name="systemd-journald",
        description="Journal Service",
        load_state="loaded",
        active_state="active",
        sub_state="running",
        definition="""[Unit]
Description=Journal Service

[Service]
ExecStart=/usr/lib/systemd/systemd-journald
""",
    ),
    UnitRecord(
        scope="system",
        type="timer",
        name="systemd-tmpfiles-clean",
        description="Daily Cleanup of Temporary Directories",
        load_state="loaded",
        active_state="active",
        sub_state="waiting",
        definition="""[Unit]
Description=Daily Cleanup of Temporary Directories

[Timer]
OnCalendar=daily
""",
    ),
    UnitRecord(
        scope="user",
        user="testuser",
        type="service",
        name="example-agent",
        description="Example user service",
        load_state="loaded",
        active_state="failed",
        sub_state="failed",
        definition="""[Unit]
Description=Example user service

[Service]
ExecStart=/usr/bin/example-agent
""",
    ),
)


def list_unit_records(
    *,
    unit_type: str | None = None,
    scope: Scope | None = None,
    user: str | None = None,
) -> tuple[UnitRecord, ...]:
    """Return matching units from the shared discovery catalog."""
    if unit_type is not None and unit_type not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported unit type: {unit_type}")

    if user == "":
        raise ValueError("user must be a non-empty string")

    if scope == "system" and user is not None:
        raise ValueError("system scope cannot specify a user")

    return tuple(
        unit
        for unit in MOCK_UNITS
        if (unit_type is None or unit.type == unit_type)
        and (scope is None or unit.scope == scope)
        and (user is None or unit.user == user)
    )


def list_unit_type_records() -> tuple[UnitTypeRecord, ...]:
    return UNIT_TYPES


def find_unit(
    *,
    scope: Scope,
    unit_type: str,
    name: str,
    user: str | None = None,
) -> UnitRecord:
    if unit_type not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported unit type: {unit_type}")

    for unit in MOCK_UNITS:
        if (
            unit.scope == scope
            and unit.type == unit_type
            and unit.name == name
            and unit.user == user
        ):
            return unit

    raise ValueError("Unit not found")


def find_unit_by_uri(uri: str) -> UnitRecord:
    parsed = urlparse(uri)
    if parsed.scheme != "systemd":
        raise ValueError("Invalid unit resource URI")

    parts = [part for part in parsed.path.split("/") if part]

    if parsed.netloc == "system" and len(parts) == 3 and parts[0] == "unit":
        _, unit_type, name = parts
        return find_unit(
            scope="system",
            unit_type=unit_type,
            name=name,
        )

    if (
        parsed.netloc == "user"
        and len(parts) == 4
        and parts[1] == "unit"
    ):
        user, _, unit_type, name = parts
        return find_unit(
            scope="user",
            user=user,
            unit_type=unit_type,
            name=name,
        )

    raise ValueError("Invalid unit resource URI")
