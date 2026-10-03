import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

from mcp_systemd import server as server_module
from mcp_systemd.config import (
    BackendConfig,
    DEFAULT_CONFIG_PATH,
    ServerConfig,
)


class CliConfigRoutingTests(unittest.TestCase):
    def _run(self, argv, config):
        mcp = mock.Mock()
        stderr = io.StringIO()

        with mock.patch.object(
            server_module,
            "load_config",
            return_value=config,
        ) as load, mock.patch.object(
            server_module,
            "build_server",
            return_value=mcp,
        ) as build, mock.patch.object(
            sys,
            "argv",
            argv,
        ):
            with contextlib.redirect_stderr(stderr):
                server_module.main()

        return load, build, mcp, stderr.getvalue()

    def test_no_config_uses_default_path_optional(self) -> None:
        config = ServerConfig()
        load, build, mcp, _ = self._run(["mcp-systemd"], config)

        load.assert_called_once_with(DEFAULT_CONFIG_PATH, required=False)
        build.assert_called_once_with(config)
        mcp.run.assert_called_once_with(
            transport="http",
            host=config.host,
            port=config.port,
        )

    def test_explicit_config_requires_path(self) -> None:
        config = ServerConfig()
        path = Path("/tmp/custom-config.yaml")
        load, _, _, _ = self._run(
            ["mcp-systemd", "--config", str(path)],
            config,
        )

        load.assert_called_once_with(path, required=True)

    def test_explicit_missing_config_exits_before_build(self) -> None:
        path = Path("/tmp/definitely-missing-config.yaml")
        stderr = io.StringIO()

        with mock.patch.object(
            server_module,
            "load_config",
            side_effect=FileNotFoundError(f"No such file: {path}"),
        ) as load, mock.patch.object(
            server_module,
            "build_server",
        ) as build, mock.patch.object(
            sys,
            "argv",
            ["mcp-systemd", "--config", str(path)],
        ):
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    server_module.main()

        self.assertNotEqual(raised.exception.code, 0)
        load.assert_called_once_with(path, required=True)
        build.assert_not_called()
        self.assertIn(str(path), stderr.getvalue())

    def test_startup_passes_configured_host_and_port(self) -> None:
        config = ServerConfig(host="127.0.0.1", port=48999)
        _, _, mcp, _ = self._run(["mcp-systemd"], config)

        mcp.run.assert_called_once_with(
            transport="http",
            host="127.0.0.1",
            port=48999,
        )

    def test_startup_emits_dbus_diagnostic(self) -> None:
        config = ServerConfig(backend=BackendConfig(type="dbus"))
        _, _, _, stderr_text = self._run(["mcp-systemd"], config)

        self.assertIn("backend=dbus", stderr_text)

    def test_startup_emits_mock_diagnostic(self) -> None:
        config = ServerConfig()
        _, _, _, stderr_text = self._run(["mcp-systemd"], config)

        self.assertIn("backend=mock", stderr_text)


if __name__ == "__main__":
    unittest.main()
