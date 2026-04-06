"""Tests for core/plugin_loader.py — plugin loading system."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from core import plugin_loader


@pytest.fixture
def plugin_dir(tmp_path):
    """Create a temp plugins directory with test plugins."""
    # Valid plugin
    (tmp_path / "greet.py").write_text(
        'TRIGGERS = ["hello", "hi"]\n'
        'DESCRIPTION = "Greeting plugin"\n'
        'def handle(message):\n'
        '    return "Hello there!"\n'
    )
    # Plugin with no triggers
    (tmp_path / "no_triggers.py").write_text(
        'def handle(message):\n'
        '    return "nope"\n'
    )
    # Plugin with no handle function
    (tmp_path / "no_handler.py").write_text(
        'TRIGGERS = ["test"]\n'
        'x = 42\n'
    )
    # Another valid plugin
    (tmp_path / "echo.py").write_text(
        'TRIGGERS = ["/echo"]\n'
        'DESCRIPTION = "Echo plugin"\n'
        'def handle(message):\n'
        '    return message.replace("/echo ", "")\n'
    )
    return tmp_path


@pytest.fixture(autouse=True)
def reset_plugins():
    """Reset plugin state before each test."""
    original_plugins = plugin_loader._plugins.copy()
    original_dir = plugin_loader._plugins_dir
    yield
    plugin_loader._plugins = original_plugins
    plugin_loader._plugins_dir = original_dir


class TestLoadPlugins:
    """Tests for load_plugins()."""

    def test_loads_valid_plugins(self, plugin_dir):
        plugin_loader.load_plugins(str(plugin_dir))
        plugins = plugin_loader.list_plugins()
        names = [p["name"] for p in plugins]
        assert "greet" in names
        assert "echo" in names

    def test_skips_plugins_without_triggers(self, plugin_dir):
        plugin_loader.load_plugins(str(plugin_dir))
        names = [p["name"] for p in plugin_loader.list_plugins()]
        assert "no_triggers" not in names

    def test_skips_plugins_without_handler(self, plugin_dir):
        plugin_loader.load_plugins(str(plugin_dir))
        names = [p["name"] for p in plugin_loader.list_plugins()]
        assert "no_handler" not in names

    def test_creates_directory_if_missing(self, tmp_path):
        new_dir = str(tmp_path / "new_plugins")
        plugin_loader.load_plugins(new_dir)
        assert os.path.exists(new_dir)
        assert plugin_loader.list_plugins() == []

    def test_handles_broken_plugin(self, tmp_path):
        (tmp_path / "broken.py").write_text("raise RuntimeError('oops')")
        plugin_loader.load_plugins(str(tmp_path))
        # Should not crash, just skip the broken plugin
        names = [p["name"] for p in plugin_loader.list_plugins()]
        assert "broken" not in names


class TestRoute:
    """Tests for route()."""

    def test_routes_to_matching_trigger(self, plugin_dir):
        plugin_loader.load_plugins(str(plugin_dir))
        result = plugin_loader.route("hello world")
        assert result == "Hello there!"

    def test_case_insensitive_trigger(self, plugin_dir):
        plugin_loader.load_plugins(str(plugin_dir))
        result = plugin_loader.route("Hello World")
        assert result == "Hello there!"

    def test_returns_none_for_no_match(self, plugin_dir):
        plugin_loader.load_plugins(str(plugin_dir))
        result = plugin_loader.route("something unrelated")
        assert result is None

    def test_returns_none_for_empty_message(self, plugin_dir):
        plugin_loader.load_plugins(str(plugin_dir))
        assert plugin_loader.route("") is None
        assert plugin_loader.route(None) is None

    def test_returns_none_for_non_string(self, plugin_dir):
        plugin_loader.load_plugins(str(plugin_dir))
        assert plugin_loader.route(123) is None

    def test_handles_plugin_error_gracefully(self, tmp_path):
        (tmp_path / "bad.py").write_text(
            'TRIGGERS = ["crash"]\n'
            'def handle(message):\n'
            '    raise ValueError("boom")\n'
        )
        plugin_loader.load_plugins(str(tmp_path))
        result = plugin_loader.route("crash now")
        assert "Plugin error" in result


class TestListPlugins:
    """Tests for list_plugins()."""

    def test_returns_plugin_metadata(self, plugin_dir):
        plugin_loader.load_plugins(str(plugin_dir))
        plugins = plugin_loader.list_plugins()
        greet = next(p for p in plugins if p["name"] == "greet")
        assert greet["description"] == "Greeting plugin"
        assert "hello" in greet["triggers"]
        assert "hi" in greet["triggers"]

    def test_returns_empty_when_no_plugins(self, tmp_path):
        plugin_loader.load_plugins(str(tmp_path / "empty_dir"))
        assert plugin_loader.list_plugins() == []


class TestReloadPlugins:
    """Tests for reload_plugins()."""

    def test_reload_refreshes_plugins(self, plugin_dir):
        plugin_loader.load_plugins(str(plugin_dir))
        initial_count = len(plugin_loader.list_plugins())

        # Add a new plugin
        (plugin_dir / "new_plugin.py").write_text(
            'TRIGGERS = ["new"]\n'
            'DESCRIPTION = "New plugin"\n'
            'def handle(message):\n'
            '    return "new!"\n'
        )
        plugin_loader.reload_plugins()
        assert len(plugin_loader.list_plugins()) == initial_count + 1
