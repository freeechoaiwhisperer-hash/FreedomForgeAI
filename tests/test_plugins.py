"""Tests for plugins — calculator, time, joke, files."""

import os
import re
from datetime import datetime
from unittest.mock import patch

import pytest

from plugins import calculator, time_plugin, joke


class TestCalculatorPlugin:
    """Tests for plugins/calculator.py."""

    def test_triggers(self):
        assert "calculate" in calculator.TRIGGERS
        assert "calc" in calculator.TRIGGERS
        assert "math" in calculator.TRIGGERS
        assert "/calc" in calculator.TRIGGERS

    def test_description_exists(self):
        assert calculator.DESCRIPTION
        assert isinstance(calculator.DESCRIPTION, str)

    def test_addition(self):
        result = calculator.handle("calc 2 + 3")
        assert "5" in result
        assert "✅" in result

    def test_multiplication(self):
        result = calculator.handle("calc 6 * 7")
        assert "42" in result

    def test_division(self):
        result = calculator.handle("calc 10 / 2")
        assert "5" in result

    def test_subtraction(self):
        result = calculator.handle("calc 10 - 3")
        assert "7" in result

    def test_complex_expression(self):
        result = calculator.handle("calc (2 + 3) * 4")
        assert "20" in result

    def test_empty_expression(self):
        result = calculator.handle("calc ")
        assert "Usage" in result

    def test_invalid_expression(self):
        result = calculator.handle("calc hello world")
        assert "❌" in result

    def test_strips_trigger_words(self):
        result = calculator.handle("calculate 1 + 1")
        assert "2" in result

    def test_no_builtin_access(self):
        """Calculator should not allow access to builtins."""
        result = calculator.handle("calc __import__('os').system('echo hi')")
        assert "❌" in result


class TestTimePlugin:
    """Tests for plugins/time_plugin.py."""

    def test_triggers(self):
        assert "what time" in time_plugin.TRIGGERS
        assert "current time" in time_plugin.TRIGGERS
        assert "/time" in time_plugin.TRIGGERS

    def test_description_exists(self):
        assert time_plugin.DESCRIPTION
        assert isinstance(time_plugin.DESCRIPTION, str)

    def test_returns_time_format(self):
        result = time_plugin.handle("what time is it")
        assert "🕒" in result
        assert "📅" in result

    def test_contains_am_or_pm(self):
        result = time_plugin.handle("/time")
        assert "AM" in result or "PM" in result

    def test_contains_date_components(self):
        result = time_plugin.handle("current time")
        now = datetime.now()
        assert now.strftime("%Y") in result


class TestJokePlugin:
    """Tests for plugins/joke.py."""

    def test_triggers(self):
        assert "joke" in joke.TRIGGERS
        assert "tell me a joke" in joke.TRIGGERS
        assert "/joke" in joke.TRIGGERS

    def test_description_exists(self):
        assert joke.DESCRIPTION
        assert isinstance(joke.DESCRIPTION, str)

    def test_returns_joke(self):
        result = joke.handle("tell me a joke")
        assert "😂" in result
        assert len(result) > 10

    def test_returns_different_jokes(self):
        """Jokes should be random — at least 2 unique results in 20 attempts."""
        results = {joke.handle("/joke") for _ in range(20)}
        assert len(results) >= 2


class TestFilesPlugin:
    """Tests for plugins/files.py."""

    def test_triggers(self):
        from plugins import files
        assert "list files" in files.TRIGGERS
        assert "show files" in files.TRIGGERS
        assert "ls" in files.TRIGGERS
        assert "/files" in files.TRIGGERS

    def test_description_exists(self):
        from plugins import files
        assert files.DESCRIPTION
        assert isinstance(files.DESCRIPTION, str)

    def test_returns_file_listing(self):
        from plugins import files
        result = files.handle("list files")
        assert "📁" in result
        # Should list some files from the app root
        assert "•" in result

    def test_hides_dotfiles(self):
        from plugins import files
        result = files.handle("ls")
        # Should not show hidden files
        assert ".git" not in result
