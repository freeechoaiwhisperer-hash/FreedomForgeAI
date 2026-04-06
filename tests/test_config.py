"""Tests for core/config.py — configuration management."""

import json
import os
import threading
import time
from unittest.mock import patch, MagicMock

import pytest


class TestLoadConfig:
    """Tests for load_config()."""

    def test_load_defaults_when_no_file(self, tmp_path):
        """When config file doesn't exist, load DEFAULTS."""
        from core import config as cfg

        fake_path = str(tmp_path / "nonexistent.json")
        original_config = cfg._config.copy()
        original_file = cfg._CONFIG_FILE

        try:
            cfg._CONFIG_FILE = fake_path
            result = cfg.load_config()
            assert result == cfg.DEFAULTS
        finally:
            cfg._CONFIG_FILE = original_file
            cfg._config = original_config

    def test_load_merges_saved_with_defaults(self, tmp_path):
        """Saved config is merged with DEFAULTS (new keys get defaults)."""
        from core import config as cfg

        config_file = tmp_path / "config.json"
        saved = {"last_model": "test-model.gguf", "n_ctx": 2048}
        config_file.write_text(json.dumps(saved))

        original_file = cfg._CONFIG_FILE
        original_config = cfg._config.copy()

        try:
            cfg._CONFIG_FILE = str(config_file)
            result = cfg.load_config()
            assert result["last_model"] == "test-model.gguf"
            assert result["n_ctx"] == 2048
            # Defaults still present for keys not in saved
            assert result["dark_mode"] == cfg.DEFAULTS["dark_mode"]
            assert result["font_size"] == cfg.DEFAULTS["font_size"]
        finally:
            cfg._CONFIG_FILE = original_file
            cfg._config = original_config

    def test_load_handles_corrupt_json(self, tmp_path):
        """Corrupt JSON file falls back to DEFAULTS."""
        from core import config as cfg

        config_file = tmp_path / "config.json"
        config_file.write_text("{invalid json!!!}")

        original_file = cfg._CONFIG_FILE
        original_config = cfg._config.copy()

        try:
            cfg._CONFIG_FILE = str(config_file)
            result = cfg.load_config()
            assert result == cfg.DEFAULTS
        finally:
            cfg._CONFIG_FILE = original_file
            cfg._config = original_config


class TestGetSet:
    """Tests for get() and set()."""

    def test_get_returns_value(self):
        from core import config as cfg

        original = cfg._config.copy()
        try:
            cfg._config = {"test_key": "test_value"}
            assert cfg.get("test_key") == "test_value"
        finally:
            cfg._config = original

    def test_get_returns_default_fallback(self):
        from core import config as cfg

        original = cfg._config.copy()
        try:
            cfg._config = {}
            result = cfg.get("nonexistent_key", "fallback_val")
            assert result == "fallback_val"
        finally:
            cfg._config = original

    def test_get_uses_DEFAULTS_before_custom_fallback(self):
        from core import config as cfg

        original = cfg._config.copy()
        try:
            cfg._config = {}
            # "n_ctx" has default of 4096
            assert cfg.get("n_ctx") == 4096
        finally:
            cfg._config = original

    def test_set_updates_config(self):
        from core import config as cfg

        original = cfg._config.copy()
        try:
            cfg._config = dict(cfg.DEFAULTS)
            with patch.object(cfg, 'save_config'):
                cfg.set("font_size", 20)
            assert cfg._config["font_size"] == 20
        finally:
            cfg._config = original


class TestFlush:
    """Tests for flush()."""

    def test_flush_writes_immediately(self, tmp_path):
        from core import config as cfg

        config_file = tmp_path / "config.json"
        original_file = cfg._CONFIG_FILE
        original_config = cfg._config.copy()

        try:
            cfg._CONFIG_FILE = str(config_file)
            cfg._config = {"test": True, "n_ctx": 2048}
            cfg.flush()

            assert config_file.exists()
            written = json.loads(config_file.read_text())
            assert written["test"] is True
            assert written["n_ctx"] == 2048
        finally:
            cfg._CONFIG_FILE = original_file
            cfg._config = original_config

    def test_flush_cancels_pending_timer(self):
        from core import config as cfg

        mock_timer = MagicMock()
        original_timer = cfg._save_timer

        try:
            cfg._save_timer = mock_timer
            with patch.object(cfg, '_write_now'):
                cfg.flush()
            mock_timer.cancel.assert_called_once()
        finally:
            cfg._save_timer = original_timer


class TestGetAll:
    """Tests for get_all()."""

    def test_get_all_returns_copy(self):
        from core import config as cfg

        original = cfg._config.copy()
        try:
            cfg._config = {"key1": "val1", "key2": "val2"}
            result = cfg.get_all()
            assert result == {"key1": "val1", "key2": "val2"}
            # Should be a copy, not the same object
            assert result is not cfg._config
        finally:
            cfg._config = original


class TestDefaults:
    """Tests for DEFAULTS structure."""

    def test_defaults_has_expected_keys(self):
        from core.config import DEFAULTS

        expected_keys = [
            "last_model", "n_ctx", "voice_in", "voice_out",
            "dark_mode", "font_size", "unlocked", "personality",
            "agent_enabled", "theme", "language", "lora_adapter",
        ]
        for key in expected_keys:
            assert key in DEFAULTS, f"Missing default key: {key}"

    def test_defaults_types(self):
        from core.config import DEFAULTS

        assert DEFAULTS["n_ctx"] == 4096
        assert DEFAULTS["voice_in"] is False
        assert DEFAULTS["dark_mode"] is True
        assert isinstance(DEFAULTS["font_size"], int)
        assert isinstance(DEFAULTS["personality"], str)
