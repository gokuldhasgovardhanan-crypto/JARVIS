import tempfile
import gc
from pathlib import Path
import pytest
from jarvis.memory.database import DatabaseManager
from jarvis.memory.repository import MemoryRepository
from jarvis.core.assistant import JarvisAssistant


@pytest.fixture
def assistant():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_mgr = DatabaseManager(Path(tmpdir) / "test.db")
        repo = MemoryRepository(db_mgr)
        ast = JarvisAssistant(repo)
        yield ast
        gc.collect()


def test_translation_intent_routing(assistant):
    res = assistant.handle("translate 'Good Morning' to German")
    assert res.action_result is not None
    assert res.action_result.intent == "translate_text"
    assert res.response_language == "de"
    assert "Translation (German)" in res.text


def test_set_preferred_language_intent(assistant):
    res = assistant.handle("set language to German")
    assert res.action_result is not None
    assert res.action_result.intent == "set_language"
    assert "German" in res.text

    # Verify persisted in database
    pref = assistant.memory.get_setting("preferred_response_language")
    assert pref == "de"


def test_switch_language_intent(assistant):
    res = assistant.handle("switch to Japanese")
    assert res.action_result is not None
    assert res.action_result.intent == "set_language"
    assert "Japanese" in res.text

    pref = assistant.memory.get_setting("preferred_response_language")
    assert pref == "ja"
