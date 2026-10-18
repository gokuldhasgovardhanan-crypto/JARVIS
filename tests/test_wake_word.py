import time
import pytest
from jarvis.voice.wake_word import WakeWordEngine


def test_wake_word_engine_initialization():
    engine = WakeWordEngine(wake_phrase="hey jarvis")
    assert engine.wake_phrase == "hey jarvis"
    assert engine.is_running is False
    assert engine._is_speaking is False


def test_echo_suppression_flag():
    engine = WakeWordEngine()
    assert engine._is_speaking is False

    engine.set_speaking_state(True)
    assert engine._is_speaking is True

    engine.set_speaking_state(False)
    assert engine._is_speaking is False


def test_debouncing_prevents_duplicates():
    triggers = []
    engine = WakeWordEngine(
        on_wake_detected=lambda: triggers.append(time.time()),
        debounce_seconds=1.5,
    )

    # First trigger
    engine._trigger_wake_word("test_source_1")
    assert len(triggers) == 1

    # Immediate second trigger within debounce window
    engine._trigger_wake_word("test_source_2")
    assert len(triggers) == 1  # Should be debounced and ignored

    # Wait past debounce window
    time.sleep(1.6)
    engine._trigger_wake_word("test_source_3")
    assert len(triggers) == 2


def test_wake_word_lifecycle():
    statuses = []
    engine = WakeWordEngine(
        on_status=lambda s: statuses.append(s),
    )
    started = engine.start()
    assert started is True
    assert engine.is_running is True

    time.sleep(0.1)
    engine.stop()
    assert engine.is_running is False
    assert any("paused" in s.lower() for s in statuses)
