"""Tests for utils/paths.py — path management and versioning."""

import os
from pathlib import Path

import pytest

from utils import paths


class TestAppVersion:
    """Tests for APP_VERSION."""

    def test_version_is_string(self):
        assert isinstance(paths.APP_VERSION, str)

    def test_version_format(self):
        # Should be semver-like
        assert "." in paths.APP_VERSION
        assert "alpha" in paths.APP_VERSION


class TestPaths:
    """Tests for path constants."""

    def test_app_root_is_path(self):
        assert isinstance(paths.APP_ROOT, Path)

    def test_app_root_exists(self):
        assert paths.APP_ROOT.exists()

    def test_models_dir_is_path(self):
        assert isinstance(paths.MODELS_DIR, Path)

    def test_logs_dir_is_path(self):
        assert isinstance(paths.LOGS_DIR, Path)

    def test_crash_dir_is_path(self):
        assert isinstance(paths.CRASH_DIR, Path)

    def test_assets_dir_is_path(self):
        assert isinstance(paths.ASSETS_DIR, Path)

    def test_config_file_is_path(self):
        assert isinstance(paths.CONFIG_FILE, Path)

    def test_key_file_is_path(self):
        assert isinstance(paths.KEY_FILE, Path)

    def test_training_dirs_are_paths(self):
        assert isinstance(paths.TRAINING_DIR, Path)
        assert isinstance(paths.ADAPTERS_DIR, Path)
        assert isinstance(paths.PRACTICE_DIR, Path)
        assert isinstance(paths.EXAMPLES_DIR, Path)
        assert isinstance(paths.RATINGS_DIR, Path)

    def test_paths_are_under_app_root(self):
        """Most paths should be under APP_ROOT."""
        for p in [paths.LOGS_DIR, paths.CRASH_DIR, paths.ASSETS_DIR,
                  paths.CONFIG_FILE, paths.KEY_FILE, paths.TRAINING_DIR]:
            assert str(paths.APP_ROOT) in str(p)


class TestEnsureDirs:
    """Tests for ensure_dirs()."""

    def test_ensure_dirs_creates_directories(self):
        """ensure_dirs should create all required directories."""
        paths.ensure_dirs()
        assert paths.LOGS_DIR.exists()
        assert paths.CRASH_DIR.exists()
        assert paths.ASSETS_DIR.exists()
        assert paths.TRAINING_DIR.exists()
        assert paths.ADAPTERS_DIR.exists()

    def test_ensure_dirs_idempotent(self):
        """Calling ensure_dirs twice doesn't raise."""
        paths.ensure_dirs()
        paths.ensure_dirs()  # Should not raise
