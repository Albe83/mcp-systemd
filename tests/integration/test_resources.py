import unittest

from mcp_systemd.domain.systemd import Systemd
from mcp_systemd.domain.unit import Scope, Unit, UnitRef
from mcp_systemd.resources import UnitResourceProvider


class MutableSystemd(Systemd):
    def __init__(self) -> None:
        self.unit = Unit(
            ref=UnitRef(
                scope="system",
                type="service",
                name="example",
            ),
            description="Example service",
            load_state="loaded",
            active_state="active",
            sub_state="running",
        )

    async def list_units(
        self,
        *,
        unit_type: str | None = None,
        scope: Scope | None = None,
        user: str | None = None,
    ) -> tuple[Unit, ...]:
        return (self.unit,)

    async def get_unit(self, ref: UnitRef) -> Unit:
        if ref != self.unit.ref:
            raise ValueError("Unit not found")
        return self.unit

    async def get_unit_definition(self, ref: UnitRef) -> str:
        return "[Unit]\nDescription=Example service\n"


class ResourceProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_resource_read_fetches_fresh_state(self) -> None:
        backend = MutableSystemd()
        provider = UnitResourceProvider(backend)

        resources = await provider._list_resources()
        resource = resources[0]

        backend.unit = Unit(
            ref=backend.unit.ref,
            description=backend.unit.description,
            load_state="loaded",
            active_state="failed",
            sub_state="failed",
        )

        content = await resource.read()

        self.assertEqual(content["active_state"], "failed")
        self.assertEqual(content["sub_state"], "failed")


if __name__ == "__main__":
    unittest.main()
