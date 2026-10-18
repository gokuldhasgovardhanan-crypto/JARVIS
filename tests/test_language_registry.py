import pytest
from jarvis.languages.registry import language_registry, LanguageSpec


def test_ten_languages_present():
    expected_codes = ["en", "ta", "hi", "te", "ml", "kn", "de", "fr", "es", "ja"]
    registered = language_registry.supported_codes()
    assert len(registered) == 10
    for code in expected_codes:
        assert code in registered, f"Missing target language: {code}"


def test_language_lookup_by_code_case_insensitive():
    spec_ta = language_registry.get("TA")
    assert spec_ta is not None
    assert spec_ta.display_name == "Tamil"
    assert spec_ta.native_name == "தமிழ்"
    assert spec_ta.code == "ta"

    spec_de = language_registry.get("de")
    assert spec_de is not None
    assert spec_de.display_name == "German"
    assert spec_de.native_name == "Deutsch"


def test_language_lookup_by_name():
    spec = language_registry.get_by_name("Japanese")
    assert spec is not None
    assert spec.code == "ja"

    spec_native = language_registry.get_by_name("हिन्दी")
    assert spec_native is not None
    assert spec_native.code == "hi"


def test_language_resolution_fallback():
    assert language_registry.resolve_language("tamil") == "ta"
    assert language_registry.resolve_language("DE") == "de"
    assert language_registry.resolve_language("unknown_alien_language", fallback="en") == "en"


def test_language_specs_have_stt_support():
    for spec in language_registry.all_languages():
        assert spec.supports_local_stt is True
        assert spec.locale != ""
        assert spec.display_name != ""
