"""Shared fixtures for FreedomForge AI tests."""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def tmp_dir(tmp_path):
    """Provide a temporary directory that is cleaned up after the test."""
    return tmp_path


@pytest.fixture
def tmp_json_file(tmp_path):
    """Create a temporary JSON file with given content."""
    def _factory(data, filename="test.json"):
        filepath = tmp_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return str(filepath)
    return _factory


@pytest.fixture
def tmp_text_file(tmp_path):
    """Create a temporary text file with given content."""
    def _factory(content, filename="test.txt"):
        filepath = tmp_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return str(filepath)
    return _factory
