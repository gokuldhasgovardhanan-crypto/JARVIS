import tempfile
import gc
from pathlib import Path
from PySide6.QtWidgets import QApplication
import pytest
from jarvis.memory.database import DatabaseManager
from jarvis.memory.repository import MemoryRepository
from jarvis.ui.settings_dialog import SettingsDialog
from jarvis.config import config


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def memory_repo():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_mgr = DatabaseManager(Path(tmpdir) / "test_settings.db")
        repo = MemoryRepository(db_mgr)
        yield repo
        gc.collect()


def test_settings_dialog_initialization(qapp, memory_repo):
    dialog = SettingsDialog(memory_repo)
    assert dialog.windowTitle() == "JARVIS Configuration & Neural Diagnostics"
    assert dialog.ai_mode_combo.count() == 3
    assert dialog.whisper_combo.count() == 4
    assert dialog.default_lang_combo.count() >= 10
    dialog.close()


def test_settings_persistence(qapp, memory_repo):
    orig_key = config.openai_api_key
    orig_mode = config.ai_mode
    orig_rate = config.speech_rate
    orig_vol = config.speech_volume
    orig_wake = config.wake_phrase

    try:
        dialog = SettingsDialog(memory_repo)
        
        # Change settings
        dialog.ai_mode_combo.setCurrentText("local")
        dialog.api_key_input.setText("sk-test-custom-key-12345")
        dialog.rate_slider.setValue(190)
        dialog.vol_slider.setValue(85)
        dialog.wake_phrase_input.setText("jarvis activate")

        # Save
        dialog._save_settings()

        # Verify config updated
        assert config.ai_mode == "local"
        assert config.openai_api_key == "sk-test-custom-key-12345"
        assert config.speech_rate == 190
        assert config.speech_volume == 0.85
        assert config.wake_phrase == "jarvis activate"

        # Verify SQLite persistence
        assert memory_repo.get_setting("ai_mode") == "local"
        assert memory_repo.get_setting("openai_api_key") == "sk-test-custom-key-12345"
        assert memory_repo.get_setting("speech_rate") == "190"
        assert memory_repo.get_setting("speech_volume") == "0.85"
        assert memory_repo.get_setting("wake_phrase") == "jarvis activate"

        # Verify a new dialog restores the saved settings
        dialog2 = SettingsDialog(memory_repo)
        assert dialog2.ai_mode_combo.currentText() == "local"
        assert dialog2.api_key_input.text() == "sk-test-custom-key-12345"
        assert dialog2.rate_slider.value() == 190
        assert dialog2.vol_slider.value() == 85
        dialog2.close()
    finally:
        config.openai_api_key = orig_key
        config.ai_mode = orig_mode
        config.speech_rate = orig_rate
        config.speech_volume = orig_vol
        config.wake_phrase = orig_wake
