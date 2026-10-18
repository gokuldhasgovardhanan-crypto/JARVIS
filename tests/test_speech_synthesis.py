import pytest
from jarvis.voice.speech_synthesis import (
    LocalSapiTTSProvider,
    CloudTTSProvider,
    TTSManager,
    VoiceCapability,
)


def test_local_sapi_availability():
    tts = LocalSapiTTSProvider()
    assert tts.is_available() is True
    voices = tts.get_available_voices()
    assert isinstance(voices, list)


def test_capability_table_all_ten_languages():
    manager = TTSManager()
    table = manager.get_capability_table()
    assert len(table) == 10
    for code in ["en", "ta", "hi", "te", "ml", "kn", "de", "fr", "es", "ja"]:
        assert code in table
        assert "display_name" in table[code]
        assert "local_voice_available" in table[code]
        assert "cloud_voice_available" in table[code]


def test_uninstalled_language_voice_fallback():
    manager = TTSManager()
    # If no local Tamil SAPI voice is installed on Windows, speak() should return False
    # and fall back to silent text rather than speaking Tamil with an English voice
    table = manager.get_capability_table()
    if not table["ta"]["local_voice_available"] and not table["ta"]["cloud_voice_available"]:
        result = manager.speak("வணக்கம்", language_code="ta")
        assert result is False


def test_tts_interrupt_stop():
    manager = TTSManager()
    # Calling stop() when idle should not error
    manager.stop()
