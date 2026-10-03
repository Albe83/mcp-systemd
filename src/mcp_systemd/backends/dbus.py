from collections.abc import Mapping, Sequence
from typing import Protocol

from dbus_fast import BusType
from dbus_fast.aio import MessageBus
from dbus_fast.errors import DBusError

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
    <method name="GetUnit">
      <arg name="name" type="s" direction="in"/>
      <arg name="unit" type="o" direction="out"/>
    </method>
  </interface>
</node>
"""
_SYSTEMD_UNIT_INTERFACE = "org.freedesktop.systemd1.Unit"
_PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"
_PROPERTIES_INTROSPECTION = """<node>
  <interface name="org.freedesktop.DBus.Properties">
    <method name="GetAll">
      <arg name="interface_name" type="s" direction="in"/>
      <arg name="properties" type="a{sv}" direction="out"/>
    </method>
  </interface>
</node>
"""
_NO_SUCH_UNIT = "org.freedesktop.systemd1.NoSuchUnit"
_UNKNOWN_OBJECT = "org.freedesktop.DBus.Error.UnknownObject"


class _SystemdManager(Protocol):
    async def call_list_units(self) -> Sequence[Sequence[object]]:
        ...

    async def call_get_unit(self, name: str) -> str:
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
        validate_unit_query(
            unit_type=ref.type,
            scope=ref.scope,
            user=ref.user,
        )

        if ref.scope == "user" or ref.user is not None:
            raise NotImplementedError(
                "user systemd managers are not supported yet"
            )

        manager = await self._system_manager()
        name = f"{ref.name}.{ref.type}"

        try:
            unit_path = await manager.call_get_unit(name)
        except DBusError as error:
            if error.type == _NO_SUCH_UNIT:
                raise ValueError("Unit not found") from error
            raise

        properties = await self._read_unit_properties(unit_path)
        return _unit_from_properties(ref, properties)

    async def _read_unit_properties(
        self,
        unit_path: str,
    ) -> Mapping[str, object]:
        bus = self._bus
        if bus is None:
            raise RuntimeError("system manager bus is not connected")

        proxy = bus.get_proxy_object(
            _SYSTEMD_BUS_NAME,
            unit_path,
            _PROPERTIES_INTROSPECTION,
        )
        properties = proxy.get_interface(_PROPERTIES_INTERFACE)

        try:
            return await properties.call_get_all(_SYSTEMD_UNIT_INTERFACE)
        except DBusError as error:
            if error.type == _UNKNOWN_OBJECT:
                raise ValueError("Unit not found") from error
            raise

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
            bus.disconnect()
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


def _unit_from_properties(
    ref: UnitRef,
    properties: Mapping[str, object],
) -> Unit:
    description = _required_string_property(properties, "Description")
    load_state = _required_string_property(properties, "LoadState")
    active_state = _required_string_property(properties, "ActiveState")
    sub_state = _required_string_property(properties, "SubState")

    if ref.type == "service":
        return ServiceUnit(
            ref=ref,
            description=description,
            load_state=load_state,
            active_state=active_state,
            sub_state=sub_state,
        )

    if ref.type == "timer":
        return TimerUnit(
            ref=ref,
            description=description,
            load_state=load_state,
            active_state=active_state,
            sub_state=sub_state,
        )

    raise ValueError(f"Unsupported unit type: {ref.type}")


def _required_string_property(
    properties: Mapping[str, object],
    key: str,
) -> str:
    try:
        variant = properties[key]
    except KeyError as error:
        raise ValueError(f"Missing unit property: {key}") from error

    value = getattr(variant, "value", None)
    if not isinstance(value, str):
        raise ValueError(f"Malformed unit property: {key}")

    return value
