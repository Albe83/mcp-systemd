import tempfile
import unittest
from pathlib import Path

from mcp_systemd.config import ServerConfig, load_config


class ConfigTests(unittest.TestCase):
    def test_missing_file_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.yaml"
            self.assertEqual(load_config(path), ServerConfig())

    def test_loads_resource_api_fallback_flag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text(
                """
server:
  host: 127.0.0.1
  port: 48001
tools:
  resource_api_fallback: false
""".lstrip(),
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 48001)
        self.assertFalse(config.resource_api_fallback)

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
