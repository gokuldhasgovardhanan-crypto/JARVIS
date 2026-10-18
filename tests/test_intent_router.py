import tempfile
import gc
from pathlib import Path
import pytest
from jarvis.memory.database import DatabaseManager
from jarvis.memory.repository import MemoryRepository
from jarvis.automation.windows_actions import WindowsActionRunner
from jarvis.core.intent_router import IntentRouter
from jarvis.core.assistant import JarvisAssistant


@pytest.fixture
def assistant():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_mgr = DatabaseManager(Path(tmpdir) / "test.db")
        repo = MemoryRepository(db_mgr)
        ast = JarvisAssistant(repo)
        yield ast
        gc.collect()


def test_time_intent(assistant):
    res = assistant.handle("what time is it")
    assert "The current time is" in res.text

    # Test Tamil query
    res_ta = assistant.handle("time sollu")
    assert "The current time is" in res_ta.text

    # Test German query
    res_de = assistant.handle("wie spät ist es")
    assert "The current time is" in res_de.text


def test_date_intent(assistant):
    res = assistant.handle("what is today's date")
    assert "Today is" in res.text

    # Test Hindi query
    res_hi = assistant.handle("aaj ki tarikh kya hai")
    assert "Today is" in res_hi.text


def test_save_and_get_notes_intent(assistant):
    # Save note via natural phrase
    res_save = assistant.handle("remember that buy organic eggs tomorrow")
    assert "I've saved that note" in res_save.text

    # Read notes back
    res_read = assistant.handle("show my notes")
    assert "buy organic eggs tomorrow" in res_read.text


def test_sensitive_clear_notes_requires_confirmation(assistant):
    assistant.handle("remember that secret plan")
    
    # Request clear notes
    res = assistant.handle("clear all notes")
    assert res.requires_confirmation is True
    assert "permanently" in res.confirmation_prompt

    # User confirms
    res_confirm = assistant.handle("yes")
    assert "Successfully purged" in res_confirm.text

    # Check notes are indeed cleared
    notes = assistant.memory.get_notes()
    assert len(notes) == 0


def test_sensitive_clear_notes_cancel(assistant):
    assistant.handle("remember that keep this note")
    res = assistant.handle("clear all notes")
    assert res.requires_confirmation is True

    # User declines
    res_cancel = assistant.handle("no")
    assert "canceled" in res_cancel.text.lower()

    # Note remains
    notes = assistant.memory.get_notes()
    assert len(notes) == 1


def test_help_intent(assistant):
    res = assistant.handle("help")
    assert "Available Commands" in res.text
    assert "get_time" in res.text
