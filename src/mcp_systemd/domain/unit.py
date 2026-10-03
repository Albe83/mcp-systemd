from dataclasses import dataclass
from typing import Literal

Scope = Literal["system", "user"]


@dataclass(frozen=True)
class UnitType:
    name: str
    description: str


@dataclass(frozen=True)
class UnitRef:
    scope: Scope
    type: str
    name: str
    user: str | None = None

    def __post_init__(self) -> None:
        if self.scope not in ("system", "user"):
            raise ValueError(f"Unsupported unit scope: {self.scope}")

        if not self.type:
            raise ValueError("unit type must be a non-empty string")

        if not self.name:
            raise ValueError("unit name must be a non-empty string")

        if self.scope == "system" and self.user is not None:
            raise ValueError("system scope cannot specify a user")

        if self.scope == "user" and not self.user:
            raise ValueError("user scope requires a user")


@dataclass(frozen=True)
class Unit:
    ref: UnitRef
    description: str
    load_state: str
    active_state: str
    sub_state: str
