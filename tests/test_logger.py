"""Tests for core/logger.py — logging system."""

import logging
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from core import logger


class TestLoggerInit:
    """Tests for logger init() and _get()."""

    def test_init_creates_log_directory(self, tmp_path):
        log_dir = str(tmp_path / "test_logs")
        with patch.object(logger, '_LOG_DIR', log_dir), \
             patch.object(logger, '_LOG_FILE', os.path.join(log_dir, "app.log")), \
             patch.object(logger, '_logger', None):
            logger.init()
            assert os.path.exists(log_dir)

    def test_init_creates_logger_instance(self, tmp_path):
        log_dir = str(tmp_path / "test_logs")
        with patch.object(logger, '_LOG_DIR', log_dir), \
             patch.object(logger, '_LOG_FILE', os.path.join(log_dir, "app.log")), \
             patch.object(logger, '_logger', None):
            logger.init()
            assert logger._logger is not None
            assert isinstance(logger._logger, logging.Logger)

    def test_get_auto_initializes(self, tmp_path):
        log_dir = str(tmp_path / "test_logs2")
        with patch.object(logger, '_LOG_DIR', log_dir), \
             patch.object(logger, '_LOG_FILE', os.path.join(log_dir, "app.log")), \
             patch.object(logger, '_logger', None):
            result = logger._get()
            assert result is not None
            assert isinstance(result, logging.Logger)

    def test_init_idempotent(self, tmp_path):
        """Calling init() twice doesn't add duplicate handlers."""
        log_dir = str(tmp_path / "test_logs3")
        with patch.object(logger, '_LOG_DIR', log_dir), \
             patch.object(logger, '_LOG_FILE', os.path.join(log_dir, "app.log")), \
             patch.object(logger, '_logger', None):
            logger.init()
            handler_count = len(logger._logger.handlers)
            logger.init()
            assert len(logger._logger.handlers) == handler_count


class TestLogFunctions:
    """Tests for convenience log functions."""

    def test_info_logs(self, tmp_path):
        log_dir = str(tmp_path / "logs")
        log_file = os.path.join(log_dir, "app.log")
        os.makedirs(log_dir, exist_ok=True)

        # Create a fresh logger with no handlers
        test_logger = logging.getLogger(f"FreedomForgeAI.test.info")
        test_logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        test_logger.addHandler(fh)

        with patch.object(logger, '_logger', test_logger):
            logger.info("test info message")

        with open(log_file, "r") as f:
            content = f.read()
        assert "test info message" in content

    def test_warning_logs(self, tmp_path):
        log_dir = str(tmp_path / "logs")
        log_file = os.path.join(log_dir, "app.log")
        os.makedirs(log_dir, exist_ok=True)

        test_logger = logging.getLogger(f"FreedomForgeAI.test.warning")
        test_logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        test_logger.addHandler(fh)

        with patch.object(logger, '_logger', test_logger):
            logger.warning("test warning message")

        with open(log_file, "r") as f:
            content = f.read()
        assert "test warning message" in content

    def test_error_logs(self, tmp_path):
        log_dir = str(tmp_path / "logs")
        log_file = os.path.join(log_dir, "app.log")
        os.makedirs(log_dir, exist_ok=True)

        test_logger = logging.getLogger(f"FreedomForgeAI.test.error")
        test_logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        test_logger.addHandler(fh)

        with patch.object(logger, '_logger', test_logger):
            logger.error("test error message")

        with open(log_file, "r") as f:
            content = f.read()
        assert "test error message" in content

    def test_debug_logs(self, tmp_path):
        log_dir = str(tmp_path / "logs")
        log_file = os.path.join(log_dir, "app.log")
        os.makedirs(log_dir, exist_ok=True)

        test_logger = logging.getLogger(f"FreedomForgeAI.test.debug")
        test_logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        test_logger.addHandler(fh)

        with patch.object(logger, '_logger', test_logger):
            logger.debug("test debug message")

        with open(log_file, "r") as f:
            content = f.read()
        assert "test debug message" in content
