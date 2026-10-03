"""Read-only diagnostic: dump native systemd D-Bus unit properties.

This is an exploratory tool used to study the native property surface before
choosing a configuration schema. It is not an MCP contract and it does not
write to systemd.
"""

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence

from dbus_fast import BusType, Variant
from dbus_fast.aio import MessageBus

SYSTEMD_BUS_NAME = "org.freedesktop.systemd1"
SYSTEMD_MANAGER_PATH = "/org/freedesktop/systemd1"
SYSTEMD_MANAGER_INTERFACE = "org.freedesktop.systemd1.Manager"
SYSTEMD_INTERFACE_PREFIX = "org.freedesktop.systemd1."
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"

SUPPORTED_UNIT_SUFFIXES = ("service", "timer")

_MANAGER_INTROSPECTION = """<node>
  <interface name="org.freedesktop.systemd1.Manager">
    <method name="GetUnit">
      <arg name="name" type="s" direction="in"/>
      <arg name="unit" type="o" direction="out"/>
    </method>
  </interface>
</node>
"""

_PROPERTIES_INTROSPECTION = """<node>
  <interface name="org.freedesktop.DBus.Properties">
    <method name="GetAll">
      <arg name="interface_name" type="s" direction="in"/>
      <arg name="properties" type="a{sv}" direction="out"/>
    </method>
  </interface>
</node>
"""


def validate_unit_name(name: str) -> str:
    stem, separator, suffix = name.rpartition(".")

    if not separator or not stem:
        raise ValueError(f"Invalid unit name: {name!r}")

    if suffix not in SUPPORTED_UNIT_SUFFIXES:
        raise ValueError(
            f"Unsupported unit name {name!r}: expected .service or .timer"
        )

    return name


def _serialize(value: object) -> object:
    if isinstance(value, Variant):
        return {
            "signature": value.signature,
            "value": _serialize(value.value),
        }

    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}

    if isinstance(value, (bytes, bytearray)):
        return list(value)

    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]

    if value is None or isinstance(value, (bool, int, float, str)):
        return value

    raise TypeError(f"Cannot serialize value of type {type(value).__name__}")


def _manager_interface(bus: MessageBus):
    proxy = bus.get_proxy_object(
        SYSTEMD_BUS_NAME,
        SYSTEMD_MANAGER_PATH,
        _MANAGER_INTROSPECTION,
    )
    return proxy.get_interface(SYSTEMD_MANAGER_INTERFACE)


def _properties_interface(bus: MessageBus, object_path: str):
    proxy = bus.get_proxy_object(
        SYSTEMD_BUS_NAME,
        object_path,
        _PROPERTIES_INTROSPECTION,
    )
    return proxy.get_interface(PROPERTIES_INTERFACE)


async def _systemd_interface_names(
    bus: MessageBus,
    object_path: str,
) -> list[str]:
    node = await bus.introspect(SYSTEMD_BUS_NAME, object_path)
    return sorted(
        interface.name
        for interface in node.interfaces
        if interface.name.startswith(SYSTEMD_INTERFACE_PREFIX)
    )


async def inspect_unit_properties(unit_name: str) -> dict[str, object]:
    validate_unit_name(unit_name)

    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    try:
        manager = _manager_interface(bus)
        object_path = await manager.call_get_unit(unit_name)

        interface_names = await _systemd_interface_names(bus, object_path)

        properties_interface = _properties_interface(bus, object_path)
        interfaces: dict[str, object] = {}
        for interface_name in interface_names:
            values = await properties_interface.call_get_all(interface_name)
            interfaces[interface_name] = {
                name: _serialize(values[name])
                for name in sorted(values)
            }
    finally:
        bus.disconnect()

    return {
        "requested_unit": unit_name,
        "object_path": object_path,
        "interfaces": interfaces,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Dump the native systemd D-Bus properties of one loaded unit "
            "(read-only developer diagnostic)."
        )
    )
    parser.add_argument(
        "unit",
        help="full unit name, for example sshd.service or logrotate.timer",
    )
    args = parser.parse_args(argv)

    try:
        unit_name = validate_unit_name(args.unit)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    try:
        result = asyncio.run(inspect_unit_properties(unit_name))
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
