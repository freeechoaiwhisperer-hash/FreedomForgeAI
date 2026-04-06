"""Tests for core/hardware.py — hardware detection and recommendations."""

from unittest.mock import patch, MagicMock
import subprocess

import pytest

from core import hardware


class TestDetectGpu:
    """Tests for detect_gpu()."""

    def test_nvidia_gpu_detected(self):
        """Successfully detects NVIDIA GPU."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"NVIDIA GeForce RTX 3080, 10240"

        with patch("subprocess.run", return_value=mock_result):
            result = hardware.detect_gpu()
            assert result["available"] is True
            assert "RTX 3080" in result["name"]
            assert result["vram_gb"] == 10
            assert result["layers"] == -1

    def test_no_nvidia_gpu(self):
        """No NVIDIA GPU returns default dict."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = hardware.detect_gpu()
            assert result["available"] is False
            assert result["name"] == "None"
            assert result["vram_gb"] == 0

    def test_nvidia_smi_fails(self):
        """nvidia-smi failure returns default."""
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("subprocess.run", return_value=mock_result):
            result = hardware.detect_gpu()
            assert result["available"] is False


class TestGetRamGb:
    """Tests for get_ram_gb()."""

    def test_returns_ram_gb(self):
        mock_vm = MagicMock()
        mock_vm.total = 16 * (1024 ** 3)  # 16 GB

        with patch.object(hardware, 'PSUTIL_AVAILABLE', True), \
             patch.object(hardware, 'psutil') as mock_psutil:
            mock_psutil.virtual_memory.return_value = mock_vm
            result = hardware.get_ram_gb()
            assert result == 16

    def test_returns_zero_without_psutil(self):
        with patch.object(hardware, 'PSUTIL_AVAILABLE', False):
            assert hardware.get_ram_gb() == 0


class TestGetCpuPercent:
    """Tests for get_cpu_percent()."""

    def test_returns_cpu_percent(self):
        with patch.object(hardware, 'PSUTIL_AVAILABLE', True), \
             patch.object(hardware, 'psutil') as mock_psutil:
            mock_psutil.cpu_percent.return_value = 45.5
            result = hardware.get_cpu_percent()
            assert result == 45.5

    def test_returns_zero_without_psutil(self):
        with patch.object(hardware, 'PSUTIL_AVAILABLE', False):
            assert hardware.get_cpu_percent() == 0.0


class TestGetGpuPercent:
    """Tests for get_gpu_percent()."""

    def test_returns_gpu_load(self):
        mock_gpu = MagicMock()
        mock_gpu.load = 0.75

        with patch.object(hardware, 'GPUTIL_AVAILABLE', True), \
             patch.object(hardware, 'GPUtil') as mock_gputil:
            mock_gputil.getGPUs.return_value = [mock_gpu]
            result = hardware.get_gpu_percent()
            assert result == 75.0

    def test_returns_zero_without_gputil(self):
        with patch.object(hardware, 'GPUTIL_AVAILABLE', False):
            assert hardware.get_gpu_percent() == 0.0

    def test_returns_zero_with_no_gpus(self):
        with patch.object(hardware, 'GPUTIL_AVAILABLE', True), \
             patch.object(hardware, 'GPUtil') as mock_gputil:
            mock_gputil.getGPUs.return_value = []
            assert hardware.get_gpu_percent() == 0.0


class TestRecommendModel:
    """Tests for recommend_model()."""

    def test_recommends_llama_3_1_for_12gb(self):
        result = hardware.recommend_model(ram_gb=16)
        assert "Llama-3.1-8B" in result

    def test_recommends_mistral_for_8gb(self):
        result = hardware.recommend_model(ram_gb=8)
        assert "mistral-7b" in result

    def test_recommends_llama_3_2_for_4gb(self):
        result = hardware.recommend_model(ram_gb=4)
        assert "Llama-3.2-3B" in result

    def test_recommends_tinyllama_for_low_ram(self):
        result = hardware.recommend_model(ram_gb=2)
        assert "tinyllama" in result

    def test_boundary_12gb(self):
        assert "Llama-3.1-8B" in hardware.recommend_model(ram_gb=12)

    def test_boundary_8gb(self):
        assert "mistral-7b" in hardware.recommend_model(ram_gb=8)

    def test_boundary_4gb(self):
        assert "Llama-3.2-3B" in hardware.recommend_model(ram_gb=4)


class TestGetSystemInfo:
    """Tests for get_system_info()."""

    def test_returns_dict_with_expected_keys(self):
        with patch.object(hardware, 'detect_gpu', return_value={"available": False}), \
             patch.object(hardware, 'get_ram_gb', return_value=8):
            info = hardware.get_system_info()
            assert "ram_gb" in info
            assert "gpu" in info
            assert info["ram_gb"] == 8


class TestGetNGpuLayers:
    """Tests for get_n_gpu_layers()."""

    def test_returns_gpu_layers(self):
        with patch.object(hardware, 'detect_gpu',
                          return_value={"layers": -1, "available": True}):
            assert hardware.get_n_gpu_layers() == -1
