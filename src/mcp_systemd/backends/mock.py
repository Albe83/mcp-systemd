from collections.abc import Iterable, Mapping

from mcp_systemd.domain.systemd import Systemd, validate_unit_query
from mcp_systemd.domain.unit import Scope, Unit, UnitRef
from mcp_systemd.domain.unit_service import ServiceUnit
from mcp_systemd.domain.unit_timer import TimerUnit

MOCK_UNITS = (
    ServiceUnit(
        ref=UnitRef(scope="system", type="service", name="sshd"),
        description="OpenSSH server daemon",
        load_state="loaded",
        active_state="active",
        sub_state="running",
    ),
    ServiceUnit(
        ref=UnitRef(scope="system", type="service", name="systemd-journald"),
        description="Journal Service",
        load_state="loaded",
        active_state="active",
        sub_state="running",
    ),
    TimerUnit(
        ref=UnitRef(scope="system", type="timer", name="systemd-tmpfiles-clean"),
        description="Daily Cleanup of Temporary Directories",
        load_state="loaded",
        active_state="active",
        sub_state="waiting",
    ),
    ServiceUnit(
        ref=UnitRef(
            scope="user",
            user="testuser",
            type="service",
            name="example-agent",
        ),
        description="Example user service",
        load_state="loaded",
        active_state="failed",
        sub_state="failed",
    ),
)

MOCK_DEFINITIONS = {
    UnitRef(scope="system", type="service", name="sshd"): """[Unit]
Description=OpenSSH server daemon

[Service]
ExecStart=/usr/sbin/sshd -D
""",
    UnitRef(
        scope="system",
        type="service",
        name="systemd-journald",
    ): """[Unit]
Description=Journal Service

[Service]
ExecStart=/usr/lib/systemd/systemd-journald
""",
    UnitRef(
        scope="system",
        type="timer",
        name="systemd-tmpfiles-clean",
    ): """[Unit]
Description=Daily Cleanup of Temporary Directories

[Timer]
OnCalendar=daily
""",
    UnitRef(
        scope="user",
        user="testuser",
        type="service",
        name="example-agent",
    ): """[Unit]
Description=Example user service

[Service]
ExecStart=/usr/bin/example-agent
""",
}


class MockSystemd(Systemd):
    """In-memory systemd adapter for development and semantic evaluation."""

    def __init__(
        self,
        *,
        units: Iterable[Unit] | None = None,
        definitions: Mapping[UnitRef, str] | None = None,
    ) -> None:
        units = MOCK_UNITS if units is None else tuple(units)
        definitions = MOCK_DEFINITIONS if definitions is None else definitions

        self._units = {unit.ref: unit for unit in units}
        self._definitions = dict(definitions)

    async def list_units(
        self,
        *,
        unit_type: str | None = None,
        scope: Scope | None = None,
        user: str | None = None,
    ) -> tuple[Unit, ...]:
        validate_unit_query(
            unit_type=unit_type,
            scope=scope,
            user=user,
        )

        return tuple(
            unit
            for unit in self._units.values()
            if (unit_type is None or unit.ref.type == unit_type)
            and (scope is None or unit.ref.scope == scope)
            and (user is None or unit.ref.user == user)
        )

    async def get_unit(self, ref: UnitRef) -> Unit:
        validate_unit_query(
            unit_type=ref.type,
            scope=ref.scope,
            user=ref.user,
        )

        try:
            return self._units[ref]
        except KeyError as error:
            raise ValueError("Unit not found") from error

    async def get_unit_definition(self, ref: UnitRef) -> str:
        await self.get_unit(ref)

        try:
            return self._definitions[ref]
        except KeyError as error:
            raise ValueError("Unit definition not found") from error
