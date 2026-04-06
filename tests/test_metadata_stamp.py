"""Tests for core/metadata_stamp.py — code metadata stamping."""

import re
from unittest.mock import patch

import pytest

from core import metadata_stamp


class TestDetectLanguage:
    """Tests for _detect_language()."""

    def test_detect_bash(self):
        assert metadata_stamp._detect_language("#!/bin/bash\necho hello") == "bash"

    def test_detect_sh(self):
        assert metadata_stamp._detect_language("#!/bin/sh\nls -la") == "bash"

    def test_detect_python_shebang(self):
        assert metadata_stamp._detect_language("#!/usr/bin/env python\nprint('hi')") == "python"

    def test_detect_python_def(self):
        assert metadata_stamp._detect_language("def my_function():\n    pass") == "python"

    def test_detect_python_import(self):
        assert metadata_stamp._detect_language("import os\nos.path.exists('/')") == "python"

    def test_detect_javascript(self):
        assert metadata_stamp._detect_language("function hello() {\n  return 1;\n}") == "javascript"

    def test_detect_javascript_arrow_not_detected(self):
        # Arrow functions without "function " keyword are not detected as JS
        # because _detect_language requires the "function " keyword for JS detection.
        # This is a known limitation in language detection.
        assert metadata_stamp._detect_language("const fn = () => {\n  return 1;\n}") == "python"

    def test_detect_c(self):
        code = '#include <stdio.h>\nint main() { return 0; }'
        assert metadata_stamp._detect_language(code) == "c"

    def test_detect_rust(self):
        assert metadata_stamp._detect_language("fn main() {\n    let mut x = 5;\n}") == "rust"

    def test_detect_go(self):
        assert metadata_stamp._detect_language("package main\nfunc main() {}") == "go"

    def test_detect_powershell(self):
        assert metadata_stamp._detect_language("# Script\nparam($Name)") == "powershell"

    def test_defaults_to_python(self):
        assert metadata_stamp._detect_language("some random text") == "python"


class TestGetStampComment:
    """Tests for _get_stamp_comment()."""

    def test_python_stamp_format(self):
        stamp = metadata_stamp._get_stamp_comment("python")
        assert stamp.startswith("# Generated:")
        assert "FFA-v1" in stamp

    def test_javascript_stamp_format(self):
        stamp = metadata_stamp._get_stamp_comment("javascript")
        assert stamp.startswith("// Generated:")
        assert "FFA-v1" in stamp

    def test_c_stamp_format(self):
        stamp = metadata_stamp._get_stamp_comment("c")
        assert stamp.startswith("/* Generated:")
        assert "FFA-v1 */" in stamp

    def test_bash_stamp_format(self):
        stamp = metadata_stamp._get_stamp_comment("bash")
        assert stamp.startswith("# Generated:")

    def test_unknown_language_defaults_to_python_style(self):
        stamp = metadata_stamp._get_stamp_comment("unknown_lang")
        assert stamp.startswith("# Generated:")

    def test_stamp_contains_ref_hash(self):
        stamp = metadata_stamp._get_stamp_comment("python")
        assert "Ref:" in stamp
        # Extract the ref hash
        ref_match = re.search(r"Ref:\s+([a-f0-9]+)", stamp)
        assert ref_match is not None
        assert len(ref_match.group(1)) == 16


class TestStampCode:
    """Tests for stamp_code()."""

    def test_stamps_python_code(self):
        code = "def hello():\n    print('Hello')"
        stamped = metadata_stamp.stamp_code(code, "python")
        lines = stamped.split("\n")
        assert lines[0].startswith("# Generated:")
        assert lines[1] == ""
        assert "def hello():" in stamped

    def test_stamps_after_shebang(self):
        code = "#!/bin/bash\necho 'hello'"
        stamped = metadata_stamp.stamp_code(code, "bash")
        lines = stamped.split("\n")
        assert lines[0] == "#!/bin/bash"
        assert lines[1].startswith("# Generated:")

    def test_skips_short_code(self):
        code = "x = 1"
        result = metadata_stamp.stamp_code(code)
        assert result == code  # Too short, not stamped

    def test_skips_empty_code(self):
        assert metadata_stamp.stamp_code("") == ""
        assert metadata_stamp.stamp_code(None) is None

    def test_auto_detects_language(self):
        code = "function test() {\n  return true;\n}"
        stamped = metadata_stamp.stamp_code(code)
        assert stamped.startswith("// Generated:")


class TestShouldStamp:
    """Tests for should_stamp()."""

    def test_stamps_python_code_block(self):
        assert metadata_stamp.should_stamp("```python\ndef hello():\n    pass\n```") is True

    def test_stamps_bash_code_block(self):
        assert metadata_stamp.should_stamp("```bash\necho hello\n```") is True

    def test_stamps_import_statement(self):
        assert metadata_stamp.should_stamp("import os\nos.path.exists('/')") is True

    def test_stamps_def_keyword(self):
        assert metadata_stamp.should_stamp("def my_function():") is True

    def test_no_stamp_for_plain_text(self):
        assert metadata_stamp.should_stamp("Hello, how are you?") is False

    def test_no_stamp_for_questions(self):
        assert metadata_stamp.should_stamp("What is the weather today?") is False


class TestStampResponse:
    """Tests for stamp_response()."""

    def test_stamps_code_blocks_in_response(self):
        response = "Here is some code:\n```python\ndef hello():\n    print('hi')\n```\nDone!"
        stamped = metadata_stamp.stamp_response(response)
        assert "Generated:" in stamped
        assert "FFA-v1" in stamped
        assert "Here is some code:" in stamped
        assert "Done!" in stamped

    def test_leaves_non_code_response_unchanged(self):
        response = "This is just a text response with no code."
        result = metadata_stamp.stamp_response(response)
        assert result == response

    def test_multiple_code_blocks(self):
        response = "```python\nimport os\nos.listdir('.')\n```\nand\n```bash\nls -la\necho done\n```"
        stamped = metadata_stamp.stamp_response(response)
        assert stamped.count("FFA-v1") == 2


class TestSessionInfo:
    """Tests for get_session_id() and get_launch_time()."""

    def test_session_id_is_hex_string(self):
        sid = metadata_stamp.get_session_id()
        assert isinstance(sid, str)
        assert len(sid) == 16
        assert all(c in "0123456789abcdef" for c in sid)

    def test_session_id_is_stable(self):
        """Session ID doesn't change within a session."""
        sid1 = metadata_stamp.get_session_id()
        sid2 = metadata_stamp.get_session_id()
        assert sid1 == sid2

    def test_launch_time_is_iso_format(self):
        lt = metadata_stamp.get_launch_time()
        assert isinstance(lt, str)
        assert "T" in lt  # ISO format
