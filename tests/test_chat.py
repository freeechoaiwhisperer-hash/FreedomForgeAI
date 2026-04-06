"""Tests for ui/chat.py — SimpleMemory, ActivityLogger, FeedbackLearner, DecisionEngine."""

import json
import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We import only the non-UI classes from ui/chat.py.
# The module imports customtkinter at top level, so we need proper mocks.
import sys
from types import ModuleType

# Create a comprehensive customtkinter mock that supports class inheritance
_mock_ctk = ModuleType('customtkinter')
_mock_ctk.CTkFrame = type('CTkFrame', (), {})
_mock_ctk.CTkLabel = type('CTkLabel', (), {})
_mock_ctk.CTkButton = type('CTkButton', (), {})
_mock_ctk.CTkTextbox = type('CTkTextbox', (), {})
_mock_ctk.CTkEntry = type('CTkEntry', (), {})
_mock_ctk.CTkFont = lambda *a, **kw: None
_mock_ctk.set_appearance_mode = lambda *a: None
sys.modules['customtkinter'] = _mock_ctk

# Mock voice modules
sys.modules.setdefault('modules.voice_listener', ModuleType('modules.voice_listener'))
sys.modules.setdefault('modules.voice_tts', ModuleType('modules.voice_tts'))

# Mock model_manager
_mock_mm = ModuleType('core.model_manager')
_mock_mm.generate = lambda *a, **kw: None
sys.modules['core.model_manager'] = _mock_mm

from ui.chat import SimpleMemory, ActivityLogger, FeedbackLearner, DecisionEngine


class TestSimpleMemory:
    """Tests for SimpleMemory class — SQLite memory backend."""

    @pytest.fixture
    def memory(self, tmp_path):
        """Create a SimpleMemory with a temp database."""
        db_path = str(tmp_path / "test_memory.db")
        return SimpleMemory(db_path=db_path)

    def test_creates_database(self, tmp_path):
        db_path = str(tmp_path / "new.db")
        mem = SimpleMemory(db_path=db_path)
        assert os.path.exists(db_path)

    def test_creates_messages_table(self, memory):
        cursor = memory.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
        )
        assert cursor.fetchone() is not None

    def test_add_message(self, memory):
        memory.add_message("user", "Hello!")
        cursor = memory.conn.execute("SELECT * FROM messages")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][1] == "user"
        assert rows[0][2] == "Hello!"

    def test_add_multiple_messages(self, memory):
        memory.add_message("user", "First")
        memory.add_message("assistant", "Second")
        memory.add_message("user", "Third")
        cursor = memory.conn.execute("SELECT COUNT(*) FROM messages")
        assert cursor.fetchone()[0] == 3

    def test_message_has_timestamp(self, memory):
        memory.add_message("user", "test")
        cursor = memory.conn.execute("SELECT timestamp FROM messages")
        ts = cursor.fetchone()[0]
        assert "T" in ts  # ISO format

    def test_search_keyword(self, memory):
        memory.add_message("user", "Tell me about Python")
        memory.add_message("assistant", "Python is a programming language")
        memory.add_message("user", "What about Java?")

        results = memory.search_keyword("Python")
        assert len(results) == 2
        assert all("Python" in r["content"] for r in results)

    def test_search_keyword_limit(self, memory):
        for i in range(10):
            memory.add_message("user", f"Message about testing {i}")

        results = memory.search_keyword("testing", limit=3)
        assert len(results) == 3

    def test_search_keyword_no_results(self, memory):
        memory.add_message("user", "Hello")
        results = memory.search_keyword("nonexistent_xyz")
        assert results == []

    def test_search_returns_dict_format(self, memory):
        memory.add_message("user", "test message")
        results = memory.search_keyword("test")
        assert len(results) == 1
        assert "role" in results[0]
        assert "content" in results[0]
        assert "timestamp" in results[0]

    def test_search_ordered_by_timestamp_desc(self, memory):
        memory.add_message("user", "search first")
        memory.add_message("user", "search second")
        memory.add_message("user", "search third")

        results = memory.search_keyword("search")
        # Most recent first
        assert "third" in results[0]["content"]
        assert "first" in results[2]["content"]


class TestActivityLogger:
    """Tests for ActivityLogger class."""

    @pytest.fixture
    def logger(self, tmp_path):
        return ActivityLogger(log_file=str(tmp_path / "activity.json"))

    def test_logs_activity(self, logger):
        logger.log_activity("chat", {"message": "hello"})
        assert len(logger.activities) == 1
        assert logger.activities[0]["type"] == "chat"
        assert logger.activities[0]["data"] == {"message": "hello"}

    def test_activity_has_timestamp(self, logger):
        logger.log_activity("test")
        assert "timestamp" in logger.activities[0]

    def test_caps_at_1000_activities(self, logger):
        for i in range(1100):
            logger.log_activity("test", {"i": i})
        assert len(logger.activities) <= 1000

    def test_saves_to_file(self, logger):
        logger.log_activity("test")
        assert os.path.exists(logger.log_file)
        with open(logger.log_file) as f:
            data = json.load(f)
        assert len(data) == 1

    def test_loads_existing_data(self, tmp_path):
        log_file = str(tmp_path / "activity.json")
        existing = [{"timestamp": "2024-01-01", "type": "old", "data": None}]
        with open(log_file, "w") as f:
            json.dump(existing, f)

        logger = ActivityLogger(log_file=log_file)
        assert len(logger.activities) == 1
        assert logger.activities[0]["type"] == "old"

    def test_handles_corrupt_file(self, tmp_path):
        log_file = str(tmp_path / "activity.json")
        with open(log_file, "w") as f:
            f.write("not valid json!!!")

        logger = ActivityLogger(log_file=log_file)
        assert logger.activities == []


class TestFeedbackLearner:
    """Tests for FeedbackLearner class."""

    @pytest.fixture
    def learner(self, tmp_path):
        return FeedbackLearner(storage_file=str(tmp_path / "feedback.json"))

    def test_record_good_feedback(self, learner):
        learner.record_feedback("How are you?", "I'm great!", is_good=True)
        assert len(learner.good_examples) == 1
        assert learner.good_examples[0] == ["How are you?", "I'm great!"]

    def test_record_bad_feedback(self, learner):
        learner.record_feedback("Hello", "ERROR", is_good=False)
        assert len(learner.bad_examples) == 1

    def test_caps_good_examples_at_20(self, learner):
        for i in range(25):
            learner.record_feedback(f"q{i}", f"a{i}", is_good=True)
        assert len(learner.good_examples) <= 20

    def test_caps_bad_examples_at_20(self, learner):
        for i in range(25):
            learner.record_feedback(f"q{i}", f"a{i}", is_good=False)
        assert len(learner.bad_examples) <= 20

    def test_saves_to_file(self, learner):
        learner.record_feedback("q", "a", is_good=True)
        assert os.path.exists(learner.storage_file)
        with open(learner.storage_file) as f:
            data = json.load(f)
        assert "good" in data
        assert "bad" in data

    def test_improve_prompt_no_examples(self, learner):
        result = learner.improve_prompt("Base prompt")
        assert result == "Base prompt"

    def test_improve_prompt_with_examples(self, learner):
        learner.record_feedback("What is AI?", "AI is artificial intelligence.", is_good=True)
        result = learner.improve_prompt("You are helpful.")
        assert "You are helpful." in result
        assert "good responses" in result
        assert "What is AI?" in result

    def test_loads_existing_data(self, tmp_path):
        storage_file = str(tmp_path / "feedback.json")
        data = {"good": [["q1", "a1"]], "bad": [["q2", "a2"]]}
        with open(storage_file, "w") as f:
            json.dump(data, f)

        learner = FeedbackLearner(storage_file=storage_file)
        assert len(learner.good_examples) == 1
        assert len(learner.bad_examples) == 1


class TestDecisionEngine:
    """Tests for DecisionEngine class."""

    @pytest.fixture
    def engine(self):
        return DecisionEngine()

    def test_routes_code_query(self, engine):
        assert engine.route("Help me with Python code") == "coder"

    def test_routes_debug_query(self, engine):
        assert engine.route("Can you debug this?") == "coder"

    def test_routes_medical_query(self, engine):
        assert engine.route("I have a medical question") == "doctor"

    def test_routes_health_query(self, engine):
        assert engine.route("How is my health?") == "doctor"

    def test_routes_science_query(self, engine):
        assert engine.route("Explain science to me") == "scientist"

    def test_routes_reasoning_query(self, engine):
        assert engine.route("Let me think about this logically") == "reasoner"

    def test_routes_general_query(self, engine):
        assert engine.route("What's the weather today?") == "general"

    def test_case_insensitive_routing(self, engine):
        assert engine.route("PYTHON help") == "coder"

    def test_get_system_prompt_coder(self, engine):
        prompt = engine.get_system_prompt("coder")
        assert "code" in prompt.lower()

    def test_get_system_prompt_doctor(self, engine):
        prompt = engine.get_system_prompt("doctor")
        assert "medical" in prompt.lower()

    def test_get_system_prompt_general(self, engine):
        prompt = engine.get_system_prompt("general")
        assert "helpful" in prompt.lower()

    def test_get_system_prompt_unknown_returns_general(self, engine):
        prompt = engine.get_system_prompt("unknown_specialist")
        assert "helpful" in prompt.lower()
