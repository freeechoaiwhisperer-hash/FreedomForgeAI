"""Tests for core/crash_reporter.py — crash reporting system."""

import json
import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from core import crash_reporter


class TestCapture:
    """Tests for capture()."""

    def test_captures_exception_and_saves_report(self, tmp_path):
        crash_dir = str(tmp_path / "crashes")
        with patch.object(crash_reporter, 'CRASH_DIR', crash_dir):
            try:
                raise ValueError("test error")
            except ValueError as e:
                report_id = crash_reporter.capture(e, context="test")

            assert report_id is not None
            assert len(report_id) == 12

            # Check file was created
            files = os.listdir(crash_dir)
            assert len(files) == 1
            assert files[0].startswith("crash_")
            assert files[0].endswith(".json")

    def test_report_contains_required_fields(self, tmp_path):
        crash_dir = str(tmp_path / "crashes")
        with patch.object(crash_reporter, 'CRASH_DIR', crash_dir):
            try:
                raise RuntimeError("boom")
            except RuntimeError as e:
                report_id = crash_reporter.capture(e, context="testing")

            files = os.listdir(crash_dir)
            with open(os.path.join(crash_dir, files[0])) as f:
                report = json.load(f)

            assert report["id"] == report_id
            assert report["error"] == "RuntimeError"
            assert report["message"] == "boom"
            assert report["context"] == "testing"
            assert "timestamp" in report
            assert "traceback" in report
            assert "system" in report
            assert "version" in report

    def test_capture_calls_on_ready(self, tmp_path):
        crash_dir = str(tmp_path / "crashes")
        callback = MagicMock()

        with patch.object(crash_reporter, 'CRASH_DIR', crash_dir):
            try:
                raise TypeError("type err")
            except TypeError as e:
                crash_reporter.capture(e, on_ready=callback)

        callback.assert_called_once()
        args = callback.call_args[0]
        assert len(args[0]) == 12  # report_id
        assert args[1].endswith(".json")  # path

    def test_capture_truncates_message(self, tmp_path):
        crash_dir = str(tmp_path / "crashes")
        with patch.object(crash_reporter, 'CRASH_DIR', crash_dir):
            long_msg = "x" * 1000
            try:
                raise ValueError(long_msg)
            except ValueError as e:
                crash_reporter.capture(e)

            files = os.listdir(crash_dir)
            with open(os.path.join(crash_dir, files[0])) as f:
                report = json.load(f)
            assert len(report["message"]) <= 500


class TestGetRecent:
    """Tests for get_recent()."""

    def test_returns_empty_when_no_crash_dir(self, tmp_path):
        crash_dir = str(tmp_path / "nonexistent")
        with patch.object(crash_reporter, 'CRASH_DIR', crash_dir):
            assert crash_reporter.get_recent() == []

    def test_returns_recent_reports(self, tmp_path):
        crash_dir = str(tmp_path / "crashes")
        with patch.object(crash_reporter, 'CRASH_DIR', crash_dir):
            for i in range(3):
                try:
                    raise ValueError(f"error {i}")
                except ValueError as e:
                    crash_reporter.capture(e)

            recent = crash_reporter.get_recent()
            assert len(recent) == 3
            assert all("id" in r for r in recent)
            assert all("error" in r for r in recent)
            assert all("path" in r for r in recent)

    def test_limits_to_10_results(self, tmp_path):
        crash_dir = str(tmp_path / "crashes")
        with patch.object(crash_reporter, 'CRASH_DIR', crash_dir):
            for i in range(15):
                try:
                    raise ValueError(f"error {i}")
                except ValueError as e:
                    crash_reporter.capture(e)

            recent = crash_reporter.get_recent()
            assert len(recent) <= 10


class TestPrune:
    """Tests for _prune()."""

    def test_prune_removes_old_reports(self, tmp_path):
        crash_dir = str(tmp_path / "crashes")
        with patch.object(crash_reporter, 'CRASH_DIR', crash_dir), \
             patch.object(crash_reporter, 'MAX_REPORTS', 3):
            for i in range(5):
                try:
                    raise ValueError(f"error {i}")
                except ValueError as e:
                    crash_reporter.capture(e)

            files = [f for f in os.listdir(crash_dir) if f.endswith(".json")]
            assert len(files) <= 3

    def test_prune_does_nothing_when_no_dir(self, tmp_path):
        with patch.object(crash_reporter, 'CRASH_DIR', str(tmp_path / "nope")):
            crash_reporter._prune()  # Should not raise


class TestSystemInfo:
    """Tests for _system_info()."""

    def test_returns_dict_with_os_info(self):
        info = crash_reporter._system_info()
        assert "os" in info
        assert "python" in info

    def test_returns_info_without_psutil(self):
        with patch.dict("sys.modules", {"psutil": None}):
            info = crash_reporter._system_info()
            assert "os" in info


class TestInstallHandler:
    """Tests for install_handler()."""

    def test_installs_excepthook(self):
        import sys
        original = sys.excepthook
        try:
            crash_reporter.install_handler()
            assert sys.excepthook != original
        finally:
            sys.excepthook = original
