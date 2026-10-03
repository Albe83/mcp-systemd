from collections.abc import Sequence
from typing import Protocol

from dbus_fast import BusType
from dbus_fast.aio import MessageBus

from mcp_systemd.domain.systemd import Systemd, validate_unit_query
from mcp_systemd.domain.unit import Scope, Unit, UnitRef
from mcp_systemd.domain.unit_service import ServiceUnit
from mcp_systemd.domain.unit_timer import TimerUnit

_SYSTEMD_BUS_NAME = "org.freedesktop.systemd1"
_SYSTEMD_MANAGER_PATH = "/org/freedesktop/systemd1"
_SYSTEMD_MANAGER_INTERFACE = "org.freedesktop.systemd1.Manager"
_SYSTEMD_MANAGER_INTROSPECTION = """<node>
  <interface name="org.freedesktop.systemd1.Manager">
    <method name="ListUnits">
      <arg name="units" type="a(ssssssouso)" direction="out"/>
    </method>
  </interface>
</node>
"""


class _SystemdManager(Protocol):
    async def call_list_units(self) -> Sequence[Sequence[object]]:
        ...


class DbusSystemd(Systemd):
    """systemd adapter backed by the system manager D-Bus API."""

    def __init__(
        self,
        *,
        manager: _SystemdManager | None = None,
    ) -> None:
        self._manager = manager
        self._bus: MessageBus | None = None

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

        if scope == "user" or user is not None:
            raise NotImplementedError(
                "user systemd managers are not supported yet"
            )

        manager = await self._system_manager()
        rows = await manager.call_list_units()

        units: list[Unit] = []
        for row in rows:
            unit = _unit_from_list_units_row(row)
            if unit is None:
                continue

            if unit_type is not None and unit.ref.type != unit_type:
                continue

            units.append(unit)

        return tuple(units)

    async def get_unit(self, ref: UnitRef) -> Unit:
        raise NotImplementedError(
            "get_unit is not implemented by DbusSystemd yet"
        )

    async def get_unit_definition(self, ref: UnitRef) -> str:
        raise NotImplementedError(
            "get_unit_definition is not implemented by DbusSystemd yet"
        )

    async def _system_manager(self) -> _SystemdManager:
        if self._manager is not None:
            return self._manager

        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        try:
            proxy = bus.get_proxy_object(
                _SYSTEMD_BUS_NAME,
                _SYSTEMD_MANAGER_PATH,
                _SYSTEMD_MANAGER_INTROSPECTION,
            )
            manager = proxy.get_interface(_SYSTEMD_MANAGER_INTERFACE)
        except Exception:
            await bus.disconnect()
            raise

        self._bus = bus
        self._manager = manager
        return manager


def _unit_from_list_units_row(
    row: Sequence[object],
) -> Unit | None:
    name = str(row[0])
    description = str(row[1])
    load_state = str(row[2])
    active_state = str(row[3])
    sub_state = str(row[4])

    stem, separator, unit_type = name.rpartition(".")
    if not separator or not stem or not unit_type:
        return None

    ref = UnitRef(
        scope="system",
        type=unit_type,
        name=stem,
    )

    if unit_type == "service":
        return ServiceUnit(
            ref=ref,
            description=description,
            load_state=load_state,
            active_state=active_state,
            sub_state=sub_state,
        )

    if unit_type == "timer":
        return TimerUnit(
            ref=ref,
            description=description,
            load_state=load_state,
            active_state=active_state,
            sub_state=sub_state,
        )

    return None
