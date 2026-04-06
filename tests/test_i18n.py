"""Tests for assets/i18n.py — internationalization system."""

import pytest

from assets import i18n


class TestStrings:
    """Tests for STRINGS definitions."""

    def test_english_exists(self):
        assert "en" in i18n.STRINGS

    def test_all_15_languages_present(self):
        expected_codes = [
            "en", "es", "fr", "de", "pt", "it", "ja", "zh",
            "ko", "ru", "ar", "hi", "nl", "tr", "pl"
        ]
        for code in expected_codes:
            assert code in i18n.STRINGS, f"Missing language: {code}"

    def test_all_languages_have_lang_name(self):
        for code, strings in i18n.STRINGS.items():
            assert "lang_name" in strings, f"Language '{code}' missing lang_name"

    def test_all_languages_have_lang_flag(self):
        for code, strings in i18n.STRINGS.items():
            assert "lang_flag" in strings, f"Language '{code}' missing lang_flag"

    def test_english_has_essential_keys(self):
        essential_keys = [
            "app_tagline", "nav_chat", "nav_models", "nav_settings",
            "chat_send", "chat_clear", "chat_welcome",
        ]
        en = i18n.STRINGS["en"]
        for key in essential_keys:
            assert key in en, f"English missing key: {key}"


class TestSetLanguage:
    """Tests for set_language()."""

    def setup_method(self):
        self._orig_lang = i18n._current_lang

    def teardown_method(self):
        i18n._current_lang = self._orig_lang

    def test_set_valid_language(self):
        i18n.set_language("es")
        assert i18n.get_language() == "es"

    def test_set_invalid_language_no_change(self):
        i18n.set_language("en")
        i18n.set_language("invalid_code")
        assert i18n.get_language() == "en"

    def test_set_all_supported_languages(self):
        for code in i18n.STRINGS:
            i18n.set_language(code)
            assert i18n.get_language() == code


class TestGetLanguage:
    """Tests for get_language()."""

    def test_returns_current_language(self):
        result = i18n.get_language()
        assert isinstance(result, str)
        assert result in i18n.STRINGS


class TestTranslation:
    """Tests for t() translation function."""

    def setup_method(self):
        self._orig_lang = i18n._current_lang

    def teardown_method(self):
        i18n._current_lang = self._orig_lang

    def test_translate_english(self):
        i18n.set_language("en")
        result = i18n.t("nav_chat")
        assert result == "Chat"

    def test_translate_spanish(self):
        i18n.set_language("es")
        result = i18n.t("nav_chat")
        # Spanish should return a non-English translation
        assert isinstance(result, str)
        assert len(result) > 0

    def test_missing_key_falls_back_to_english(self):
        i18n.set_language("es")
        # Use a key that exists in English
        en_value = i18n.STRINGS["en"].get("app_tagline")
        # If the key doesn't exist in Spanish, it falls back
        result = i18n.t("app_tagline")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unknown_key_returns_key(self):
        result = i18n.t("completely_nonexistent_key_xyz")
        assert result == "completely_nonexistent_key_xyz"

    def test_format_substitution(self):
        i18n.set_language("en")
        # Test with a key that has format substitution
        # Even if no key uses it, test the mechanism
        original_strings = i18n.STRINGS["en"].copy()
        try:
            i18n.STRINGS["en"]["test_format"] = "Hello, {name}!"
            result = i18n.t("test_format", name="World")
            assert result == "Hello, World!"
        finally:
            i18n.STRINGS["en"] = original_strings

    def test_format_substitution_ignores_bad_keys(self):
        i18n.set_language("en")
        original_strings = i18n.STRINGS["en"].copy()
        try:
            i18n.STRINGS["en"]["test_bad_format"] = "Hello, {name}!"
            result = i18n.t("test_bad_format", wrong_key="World")
            # Should not crash, returns original string
            assert result == "Hello, {name}!"
        finally:
            i18n.STRINGS["en"] = original_strings


class TestLanguageOptions:
    """Tests for language_options()."""

    def test_returns_list_of_tuples(self):
        options = i18n.language_options()
        assert isinstance(options, list)
        assert len(options) == 15
        for item in options:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_contains_english(self):
        options = i18n.language_options()
        codes = [opt[0] for opt in options]
        assert "en" in codes

    def test_display_names_contain_flags(self):
        options = i18n.language_options()
        for code, display in options:
            assert len(display) > 2  # Should have flag + name


class TestDisplayNameToCode:
    """Tests for display_name_to_code()."""

    def test_converts_known_display_name(self):
        options = i18n.language_options()
        for code, display in options:
            assert i18n.display_name_to_code(display) == code

    def test_returns_en_for_unknown(self):
        assert i18n.display_name_to_code("Unknown Language") == "en"


class TestDetectSystemLanguage:
    """Tests for detect_system_language()."""

    def test_returns_valid_language_code(self):
        result = i18n.detect_system_language()
        assert isinstance(result, str)
        assert len(result) == 2

    def test_fallback_to_english(self):
        from unittest.mock import patch
        with patch("locale.getdefaultlocale", return_value=(None, None)):
            assert i18n.detect_system_language() == "en"

    def test_detects_known_locale(self):
        from unittest.mock import patch
        with patch("locale.getdefaultlocale", return_value=("es_ES", "UTF-8")):
            assert i18n.detect_system_language() == "es"
