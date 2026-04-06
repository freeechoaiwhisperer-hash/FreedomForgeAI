"""Tests for core/network_monitor.py — network monitoring."""

import platform
from unittest.mock import patch, MagicMock
import subprocess

import pytest

from core import network_monitor


class TestPlatformDetection:
    """Tests for platform constants."""

    def test_platform_constants_are_booleans(self):
        assert isinstance(network_monitor.IS_LINUX, bool)
        assert isinstance(network_monitor.IS_MAC, bool)
        assert isinstance(network_monitor.IS_WIN, bool)

    def test_only_one_platform_true(self):
        """At most one platform should be True."""
        platforms = [network_monitor.IS_LINUX, network_monitor.IS_MAC, network_monitor.IS_WIN]
        assert sum(platforms) <= 1


class TestRun:
    """Tests for _run() helper."""

    def test_run_success(self):
        result = network_monitor._run(["echo", "hello"])
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_run_failure(self):
        result = network_monitor._run(["false"])
        assert result.returncode != 0

    def test_run_handles_missing_command(self):
        result = network_monitor._run(["nonexistent_cmd_12345"])
        assert result.returncode != 0


class TestGetConnections:
    """Tests for get_connections() and platform-specific helpers."""

    def test_get_connections_returns_list(self):
        """Sync call should return a list."""
        result = network_monitor.get_connections(callback=None)
        assert isinstance(result, list)

    def test_connections_with_callback(self):
        callback = MagicMock()
        network_monitor.get_connections(callback=callback)
        import time
        time.sleep(1)
        callback.assert_called_once()
        args = callback.call_args[0]
        assert isinstance(args[0], list)


class TestConnsLinux:
    """Tests for _conns_linux() parsing."""

    def test_parses_ss_output(self):
        mock_output = (
            "Netid  State  Recv-Q Send-Q  Local Address:Port  Peer Address:Port\n"
            "tcp    ESTAB  0      0       192.168.1.1:45678   8.8.8.8:443       users:((\"firefox\",pid=1234,fd=5))\n"
        )
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output

        with patch.object(network_monitor, '_run', return_value=mock_result):
            conns = network_monitor._conns_linux()
            assert len(conns) >= 1
            assert conns[0]["name"] == "firefox"

    def test_handles_ss_failure(self):
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch.object(network_monitor, '_run', return_value=mock_result):
            assert network_monitor._conns_linux() == []


class TestGetBandwidth:
    """Tests for get_bandwidth()."""

    def test_returns_bandwidth_dict(self):
        mock_counters = MagicMock()
        mock_counters.bytes_sent = 1024 * 1024 * 100  # 100 MB
        mock_counters.bytes_recv = 1024 * 1024 * 200  # 200 MB

        with patch.dict("sys.modules", {"psutil": MagicMock()}):
            import sys
            sys.modules["psutil"].net_io_counters.return_value = mock_counters
            result = network_monitor.get_bandwidth(callback=None)
            assert isinstance(result, dict)
            assert "mb_sent" in result
            assert "mb_recv" in result

    def test_bandwidth_with_callback(self):
        callback = MagicMock()
        network_monitor.get_bandwidth(callback=callback)
        import time
        time.sleep(1)
        callback.assert_called_once()


class TestCheckVpnInstalled:
    """Tests for check_vpn_installed()."""

    def test_returns_dict_with_vpn_names(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = network_monitor.check_vpn_installed()
            assert isinstance(result, dict)
            assert "mullvad" in result
            assert "protonvpn" in result
            assert "wireguard" in result
            assert "openvpn" in result

    def test_all_false_when_not_installed(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = network_monitor.check_vpn_installed()
            assert all(v is False for v in result.values())


class TestGetVpnStatus:
    """Tests for get_vpn_status()."""

    def test_not_connected_by_default(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = network_monitor.get_vpn_status()
            assert result["connected"] is False
            assert result["provider"] is None

    def test_detects_mullvad(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Connected to Mullvad"

        with patch("subprocess.run", return_value=mock_result):
            result = network_monitor.get_vpn_status()
            assert result["connected"] is True
            assert result["provider"] == "Mullvad"


class TestAsync:
    """Tests for _async() helper."""

    def test_sync_mode_returns_result(self):
        def my_func():
            return 42
        result = network_monitor._async(my_func, None)
        assert result == 42

    def test_async_mode_calls_callback(self):
        callback = MagicMock()
        def my_func():
            return 42
        network_monitor._async(my_func, callback)
        import time
        time.sleep(0.5)
        callback.assert_called_once_with(42)

    def test_async_mode_handles_error(self):
        callback = MagicMock()
        def my_func():
            raise RuntimeError("boom")
        network_monitor._async(my_func, callback)
        import time
        time.sleep(0.5)
        callback.assert_called_once()
        assert isinstance(callback.call_args[0][0], RuntimeError)
