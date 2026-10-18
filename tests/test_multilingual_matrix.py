import tempfile
import gc
from pathlib import Path
import pytest
from jarvis.languages.registry import language_registry
from jarvis.languages.policies import policy_engine
from jarvis.voice.language_detection import LanguageDetectionService
from jarvis.voice.speech_synthesis import TTSManager
from jarvis.memory.database import DatabaseManager
from jarvis.memory.repository import MemoryRepository
from jarvis.core.assistant import JarvisAssistant


@pytest.fixture
def assistant():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_mgr = DatabaseManager(Path(tmpdir) / "test_matrix.db")
        repo = MemoryRepository(db_mgr)
        ast = JarvisAssistant(repo)
        yield ast
        gc.collect()


# 10 Languages Test Matrix
LANGUAGE_CASES = [
    ("en", "what time is it", "The current time is"),
    ("ta", "time sollu", "The current time is"),
    ("hi", "samay batao", "The current time is"),
    ("te", "theedi cheppu", "Today is"),
    ("ml", "thiyathi parayu", "Today is"),
    ("kn", "dinaanka heli", "Today is"),
    ("de", "wie spät ist es", "The current time is"),
    ("fr", "quelle heure est-il", "The current time is"),
    ("es", "qué hora es", "The current time is"),
    ("ja", "今何時ですか", "The current time is"),
]


@pytest.mark.parametrize("lang_code,query,expected_snippet", LANGUAGE_CASES)
def test_all_ten_languages_intent_routing(assistant, lang_code, query, expected_snippet):
    """Verifies that intent routing responds correctly across all 10 target languages."""
    res = assistant.handle(query)
    assert expected_snippet in res.text


def test_ten_languages_registry_and_tts_capabilities():
    """Verifies that all 10 languages exist in registry and have TTS capability definitions."""
    tts = TTSManager()
    table = tts.get_capability_table()
    
    expected_codes = ["en", "ta", "hi", "te", "ml", "kn", "de", "fr", "es", "ja"]
    for code in expected_codes:
        spec = language_registry.get(code)
        assert spec is not None, f"Language {code} missing from registry!"
        assert code in table, f"Language {code} missing from TTS capability table!"
        assert "display_name" in table[code]


def test_policy_engine_matrix_resolution():
    """Verifies that policy engine correctly respects explicit and auto preferences across languages."""
    for code in ["en", "ta", "hi", "te", "ml", "kn", "de", "fr", "es", "ja"]:
        # When user explicitly prefers this language
        dec = policy_engine.determine_response_language(detected_language="en", user_preference=code)
        assert dec.response_language == code

        # When set to auto, mirrors detected language
        dec_auto = policy_engine.determine_response_language(detected_language=code, user_preference="auto")
        assert dec_auto.response_language == code
