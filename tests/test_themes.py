"""Tests for assets/themes.py — theme system."""

import pytest

from assets import themes


class TestThemesData:
    """Tests for theme definitions."""

    def test_all_themes_exist(self):
        expected = ["Midnight", "Forge", "Aurora", "Ghost", "Matrix"]
        for name in expected:
            assert name in themes.THEMES

    def test_each_theme_has_required_keys(self):
        required_keys = [
            "display", "base", "bg_deep", "bg_panel", "bg_card",
            "bg_input", "accent", "text_primary", "text_secondary",
            "green", "red", "yellow", "border",
        ]
        for name, theme in themes.THEMES.items():
            for key in required_keys:
                assert key in theme, f"Theme '{name}' missing key '{key}'"

    def test_base_is_dark_or_light(self):
        for name, theme in themes.THEMES.items():
            assert theme["base"] in ("dark", "light"), \
                f"Theme '{name}' has invalid base: {theme['base']}"

    def test_ghost_is_light_theme(self):
        assert themes.THEMES["Ghost"]["base"] == "light"

    def test_midnight_is_dark_theme(self):
        assert themes.THEMES["Midnight"]["base"] == "dark"

    def test_color_values_are_hex(self):
        import re
        hex_pattern = re.compile(r'^#[0-9a-fA-F]{6}$')
        color_keys = [
            "bg_deep", "bg_panel", "bg_card", "bg_input",
            "accent", "text_primary", "border",
        ]
        for name, theme in themes.THEMES.items():
            for key in color_keys:
                assert hex_pattern.match(theme[key]), \
                    f"Theme '{name}', key '{key}' has non-hex value: {theme[key]}"


class TestDefaultTheme:
    """Tests for DEFAULT_THEME."""

    def test_default_theme_exists(self):
        assert themes.DEFAULT_THEME in themes.THEMES

    def test_default_is_midnight(self):
        assert themes.DEFAULT_THEME == "Midnight"


class TestGet:
    """Tests for get()."""

    def test_get_existing_theme(self):
        theme = themes.get("Forge")
        assert theme["display"] == "🔥  Forge"
        assert theme["base"] == "dark"

    def test_get_nonexistent_returns_default(self):
        theme = themes.get("NonexistentTheme")
        default = themes.THEMES[themes.DEFAULT_THEME]
        assert theme == default


class TestNames:
    """Tests for names()."""

    def test_returns_all_theme_names(self):
        result = themes.names()
        assert isinstance(result, list)
        assert "Midnight" in result
        assert "Ghost" in result
        assert len(result) == 5


class TestDisplayNames:
    """Tests for display_names()."""

    def test_returns_display_names(self):
        result = themes.display_names()
        assert isinstance(result, list)
        assert len(result) == 5
        assert "🌑  Midnight" in result
        assert "🔥  Forge" in result


class TestNameFromDisplay:
    """Tests for name_from_display()."""

    def test_finds_name_from_display(self):
        assert themes.name_from_display("🌑  Midnight") == "Midnight"
        assert themes.name_from_display("🔥  Forge") == "Forge"
        assert themes.name_from_display("👻  Ghost") == "Ghost"

    def test_returns_default_for_unknown_display(self):
        result = themes.name_from_display("Unknown Display Name")
        assert result == themes.DEFAULT_THEME
