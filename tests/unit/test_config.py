import tempfile
import unittest
from pathlib import Path

from mcp_systemd.config import (
    BackendConfig,
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


class BackendConfigTests(unittest.TestCase):
    def test_defaults_to_mock(self) -> None:
        self.assertEqual(BackendConfig().type, "mock")

    def test_accepts_known_types(self) -> None:
        self.assertEqual(BackendConfig(type="mock").type, "mock")
        self.assertEqual(BackendConfig(type="dbus").type, "dbus")

    def test_rejects_unknown_and_non_canonical_types(self) -> None:
        for value in ("Mock", "DBUS", "systemd", "", "  "):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "backend type"):
                    BackendConfig(type=value)

    def test_rejects_non_string_types(self) -> None:
        for value in (None, True, 1, ["mock"], {"type": "mock"}):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "backend type"):
                    BackendConfig(type=value)


class BackendConfigFileTests(unittest.TestCase):
    def _write(self, directory: str, text: str) -> Path:
        path = Path(directory) / "config.yaml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_absent_backend_defaults_to_mock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, "server:\n  port: 48001\n")
            self.assertEqual(load_config(path).backend, BackendConfig())

    def test_empty_backend_mapping_defaults_to_mock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, "backend: {}\n")
            self.assertEqual(load_config(path).backend.type, "mock")

    def test_loads_dbus_backend(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, "backend:\n  type: dbus\n")
            self.assertEqual(load_config(path).backend.type, "dbus")

    def test_rejects_non_mapping_backend(self) -> None:
        for text in (
            "backend: null\n",
            "backend: dbus\n",
            "backend: [dbus]\n",
        ):
            with self.subTest(text=text):
                with tempfile.TemporaryDirectory() as directory:
                    path = self._write(directory, text)
                    with self.assertRaisesRegex(
                        ValueError,
                        "backend must be a mapping",
                    ):
                        load_config(path)

    def test_rejects_invalid_backend_type(self) -> None:
        for value in ('null', 'true', '1', '""', '" "', 'Mock', 'DBUS'):
            with self.subTest(value=value):
                with tempfile.TemporaryDirectory() as directory:
                    path = self._write(
                        directory,
                        f"backend:\n  type: {value}\n",
                    )
                    with self.assertRaisesRegex(ValueError, "backend type"):
                        load_config(path)

    def test_rejects_unknown_backend_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, "backend:\n  typo: dbus\n")
            with self.assertRaisesRegex(
                ValueError,
                "Unknown backend configuration",
            ):
                load_config(path)

    def test_rejects_unknown_root_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, "backed:\n  type: dbus\n")
            with self.assertRaisesRegex(
                ValueError,
                "Unknown configuration keys",
            ):
                load_config(path)

    def test_rejects_non_string_root_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, "1: true\n")
            with self.assertRaisesRegex(
                ValueError,
                "Unknown configuration keys",
            ):
                load_config(path)

    def test_rejects_falsey_non_mapping_roots(self) -> None:
        for text in ("false\n", "0\n", '""\n', "[]\n"):
            with self.subTest(text=text):
                with tempfile.TemporaryDirectory() as directory:
                    path = self._write(directory, text)
                    with self.assertRaisesRegex(
                        ValueError,
                        "configuration root must be a mapping",
                    ):
                        load_config(path)

    def test_empty_document_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, "")
            self.assertEqual(load_config(path), ServerConfig())

    def test_missing_optional_file_returns_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.yaml"
            self.assertEqual(load_config(path), ServerConfig())
            self.assertEqual(
                load_config(path, required=False),
                ServerConfig(),
            )

    def test_missing_required_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.yaml"
            with self.assertRaises(FileNotFoundError):
                load_config(path, required=True)


if __name__ == "__main__":
    unittest.main()
