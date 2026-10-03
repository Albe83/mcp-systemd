import unittest

from mcp_systemd.config import ServerConfig, ToolExposureConfig
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

    async def test_group_can_hide_resource_fallback_tools(self) -> None:
        mcp = build_server(
            ServerConfig(
                tools=ToolExposureConfig(
                    groups={"resource_api_fallback": False},
                )
            )
        )
        names = {tool.name for tool in await mcp.list_tools()}

        self.assertNotIn("list_units", names)
        self.assertNotIn("read_unit", names)
        self.assertNotIn("read_unit_definition", names)
        self.assertIn("list_unit_types", names)

    async def test_explicit_enable_overrides_group(self) -> None:
        mcp = build_server(
            ServerConfig(
                tools=ToolExposureConfig(
                    groups={"resource_api_fallback": False},
                    enable=frozenset({"read_unit"}),
                )
            )
        )
        names = {tool.name for tool in await mcp.list_tools()}

        self.assertNotIn("list_units", names)
        self.assertIn("read_unit", names)
        self.assertNotIn("read_unit_definition", names)
        self.assertIn("list_unit_types", names)

    async def test_explicit_disable_hides_individual_tool(self) -> None:
        mcp = build_server(
            ServerConfig(
                tools=ToolExposureConfig(
                    groups={"resource_api_fallback": True},
                    disable=frozenset({"read_unit_definition"}),
                )
            )
        )
        names = {tool.name for tool in await mcp.list_tools()}

        self.assertIn("list_units", names)
        self.assertIn("read_unit", names)
        self.assertNotIn("read_unit_definition", names)
        self.assertIn("list_unit_types", names)

    async def test_unknown_tool_override_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Unknown tool name in configuration",
        ):
            build_server(
                ServerConfig(
                    tools=ToolExposureConfig(
                        enable=frozenset({"does_not_exist"}),
                    )
                )
            )

    async def test_backend_can_be_injected_at_composition_root(self) -> None:
        from mcp_systemd.backends.mock import MockSystemd

        mcp = build_server(
            ServerConfig(),
            systemd=MockSystemd(units=(), definitions={}),
        )
        self.assertEqual(await mcp.list_resources(), [])

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
