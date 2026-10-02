import unittest

from mcp_systemd.config import ServerConfig
from mcp_systemd.server import build_server


class ServerSurfaceTests(unittest.IsolatedAsyncioTestCase):
    async def test_default_surface_includes_resource_fallback_tools(self) -> None:
        mcp = build_server(ServerConfig())
        names = {tool.name for tool in await mcp.list_tools()}

        self.assertTrue(
            {
                "list_units",
                "read_unit",
                "read_unit_definition",
                "list_unit_types",
            }.issubset(names)
        )

    async def test_fallback_can_be_disabled_without_hiding_unit_types(self) -> None:
        mcp = build_server(ServerConfig(resource_api_fallback=False))
        names = {tool.name for tool in await mcp.list_tools()}

        self.assertNotIn("list_units", names)
        self.assertNotIn("read_unit", names)
        self.assertNotIn("read_unit_definition", names)
        self.assertIn("list_unit_types", names)

    async def test_resources_list_contains_base_units_from_multiple_managers(
        self,
    ) -> None:
        mcp = build_server(ServerConfig())
        uris = {str(resource.uri) for resource in await mcp.list_resources()}

        self.assertIn("systemd://system/unit/service/sshd", uris)
        self.assertIn(
            "systemd://user/testuser/unit/service/example-agent",
            uris,
        )
        self.assertFalse(any(uri.endswith("/definition") for uri in uris))


if __name__ == "__main__":
    unittest.main()
