import tempfile
import unittest
from pathlib import Path

from mcp_systemd.config import (
    ServerConfig,
    ToolExposureConfig,
    load_config,
)


class ToolExposureConfigTests(unittest.TestCase):
    def test_tool_without_groups_is_enabled_by_default(self) -> None:
        config = ToolExposureConfig()
        self.assertTrue(config.is_enabled("list_unit_types"))

    def test_disabled_group_hides_member(self) -> None:
        config = ToolExposureConfig(
            groups={"resource_api_fallback": False},
        )
        self.assertFalse(
            config.is_enabled(
                "read_unit",
                groups=frozenset({"resource_api_fallback"}),
            )
        )

    def test_explicit_enable_overrides_disabled_group(self) -> None:
        config = ToolExposureConfig(
            groups={"resource_api_fallback": False},
            enable=frozenset({"read_unit"}),
        )
        self.assertTrue(
            config.is_enabled(
                "read_unit",
                groups=frozenset({"resource_api_fallback"}),
            )
        )

    def test_explicit_disable_overrides_enabled_group(self) -> None:
        config = ToolExposureConfig(
            groups={"resource_api_fallback": True},
            disable=frozenset({"read_unit"}),
        )
        self.assertFalse(
            config.is_enabled(
                "read_unit",
                groups=frozenset({"resource_api_fallback"}),
            )
        )

    def test_all_groups_must_be_enabled(self) -> None:
        config = ToolExposureConfig(
            groups={
                "one": True,
                "two": False,
            },
        )
        self.assertFalse(
            config.is_enabled(
                "example",
                groups=frozenset({"one", "two"}),
            )
        )


class ConfigTests(unittest.TestCase):
    def test_missing_file_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.yaml"
            self.assertEqual(load_config(path), ServerConfig())

    def test_loads_tool_groups_and_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text(
                """
server:
  host: 127.0.0.1
  port: 48001
tools:
  groups:
    resource_api_fallback: false
  enable:
    - read_unit
  disable:
    - read_unit_definition
""".lstrip(),
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 48001)
        self.assertFalse(config.tools.groups["resource_api_fallback"])
        self.assertEqual(config.tools.enable, frozenset({"read_unit"}))
        self.assertEqual(
            config.tools.disable,
            frozenset({"read_unit_definition"}),
        )

    def test_rejects_non_mapping_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text("- invalid\n- root\n", encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                "configuration root must be a mapping",
            ):
                load_config(path)

    def test_rejects_non_mapping_tools_section(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text("tools: false\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "tools must be a mapping"):
                load_config(path)

    def test_rejects_unknown_tool_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text(
                "tools:\n  resource_api_fallback: false\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "Unknown tools configuration",
            ):
                load_config(path)

    def test_rejects_unknown_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text(
                "tools:\n  groups:\n    typo: true\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Unknown tool group"):
                load_config(path)

    def test_rejects_non_boolean_group_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text(
                "tools:\n  groups:\n    resource_api_fallback: \"true\"\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "tools.groups values must be booleans",
            ):
                load_config(path)

    def test_rejects_enable_disable_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text(
                """
tools:
  enable:
    - read_unit
  disable:
    - read_unit
""".lstrip(),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "tools.enable and tools.disable overlap",
            ):
                load_config(path)

    def test_rejects_boolean_port(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text("server:\n  port: true\n", encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                "server.port must be an integer between 1 and 65535",
            ):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
