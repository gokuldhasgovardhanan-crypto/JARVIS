import pytest
from jarvis.voice.language_detection import LanguageDetectionService, LanguageDetectionResult


@pytest.fixture
def detector():
    return LanguageDetectionService(fallback_language="en")


def test_native_script_detection(detector):
    # Tamil script
    res_ta = detector.detect("வணக்கம் ஜார்விஸ்")
    assert res_ta.language == "ta"
    assert res_ta.confidence >= 0.85
    assert res_ta.is_uncertain is False
    assert res_ta.method == "script_analysis"

    # Hindi Devanagari script
    res_hi = detector.detect("नमस्ते जार्विस आप कैसे हैं")
    assert res_hi.language == "hi"
    assert res_hi.confidence >= 0.85
    assert res_hi.is_uncertain is False

    # Japanese script
    res_ja = detector.detect("こんにちは、ジャービス")
    assert res_ja.language == "ja"
    assert res_ja.confidence >= 0.85


def test_romanized_mixed_language_code_switching(detector):
    # Tamil-English (Tanglish)
    res_tanglish = detector.detect("Jarvis, Notepad open pannu")
    assert res_tanglish.language == "ta"
    assert res_tanglish.confidence >= 0.70
    assert res_tanglish.method == "romanized_markers"

    # Hindi-English (Hinglish)
    res_hinglish = detector.detect("Jarvis Notepad kholo aur samay batao")
    assert res_hinglish.language == "hi"
    assert res_hinglish.confidence >= 0.70


def test_european_latin_languages(detector):
    # German
    res_de = detector.detect("Öffne Notepad und erkläre mir künstliche Intelligenz")
    assert res_de.language == "de"
    assert res_de.is_uncertain is False

    # French
    res_fr = detector.detect("Bonjour Jarvis, ouvre la calculatrice s'il vous plaît")
    assert res_fr.language == "fr"

    # Spanish
    res_es = detector.detect("Hola Jarvis, por favor abre la calculadora hoy")
    assert res_es.language == "es"


def test_short_phrase_uncertainty_and_context(detector):
    # Ambiguous short single-word token
    res_short = detector.detect("calc")
    assert res_short.is_uncertain is True

    # With previous language context
    res_context = detector.detect("calc", previous_language="de")
    assert res_context.language == "de"
    assert res_context.method == "context_prior"
