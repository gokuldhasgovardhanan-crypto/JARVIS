from typing import Optional, List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QSlider,
    QTabWidget,
    QFrame,
    QMessageBox,
)
from jarvis.config import config
from jarvis.memory.repository import MemoryRepository
from jarvis.languages.registry import language_registry
from jarvis.voice.audio_input import AudioInputService, AudioDeviceInfo
from jarvis.voice.speech_synthesis import TTSManager
from jarvis.utils.logging_config import logger


SETTINGS_STYLE = """
QDialog {
    background-color: #06111e;
    color: #d8f7ff;
    font-family: 'Segoe UI', -apple-system, sans-serif;
}
QTabWidget::pane {
    border: 1px solid #14384d;
    background-color: #081726;
    border-radius: 6px;
    padding: 8px;
}
QTabBar::tab {
    background-color: #050d17;
    color: #689cb5;
    padding: 8px 18px;
    margin-right: 4px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-size: 11px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background-color: #081726;
    color: #00e5ff;
    border-bottom: 2px solid #00e5ff;
}
QLabel {
    color: #8cbcd1;
    font-size: 11px;
    font-weight: 500;
}
QLineEdit, QComboBox {
    background-color: #0d2238;
    color: #ffffff;
    border: 1px solid #1c4b69;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #00e5ff;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #0d2238;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #00e5ff;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    border: 1px solid #00e5ff;
    width: 14px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 7px;
}
QPushButton {
    background-color: #0d253a;
    color: #aae5f7;
    border: 1px solid #1f4f6e;
    border-radius: 4px;
    padding: 7px 16px;
    font-size: 11px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #143552;
    border-color: #00e5ff;
    color: #ffffff;
}
QPushButton#primary {
    background-color: #00e5ff;
    color: #040d12;
    border: none;
    font-weight: bold;
}
QPushButton#primary:hover {
    background-color: #66efff;
}
"""


class SettingsDialog(QDialog):
    """Futuristic HUD configuration modal for AI, speech, languages, and hardware."""

    settings_updated = Signal()

    def __init__(self, memory_repo: MemoryRepository, tts_manager: Optional[TTSManager] = None, parent=None):
        super().__init__(parent)
        self.memory = memory_repo
        self.tts = tts_manager
        self.setWindowTitle("JARVIS Configuration & Neural Diagnostics")
        self.resize(580, 520)
        self.setStyleSheet(SETTINGS_STYLE)

        self._build_ui()
        self._load_current_settings()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(14)

        # Header
        header = QVBoxLayout()
        header.setSpacing(2)
        eyebrow = QLabel("SYSTEM CONFIGURATION MATRIX")
        eyebrow.setStyleSheet("color: #00e5ff; font-size: 10px; letter-spacing: 2px; font-weight: bold;")
        title = QLabel("J.A.R.V.I.S. PREFERENCES")
        title.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        header.addWidget(eyebrow)
        header.addWidget(title)
        main_layout.addLayout(header)

        # Tab Widget
        tabs = QTabWidget()

        # Tab 1: AI & Brain
        tab_ai = QWidget()
        ai_layout = QVBoxLayout(tab_ai)
        ai_layout.setSpacing(10)

        ai_layout.addWidget(QLabel("AI EXECUTION MODE"))
        self.ai_mode_combo = QComboBox()
        self.ai_mode_combo.addItems(["hybrid", "local", "cloud"])
        ai_layout.addWidget(self.ai_mode_combo)

        ai_layout.addWidget(QLabel("OPENAI API KEY (Cloud Neural Engine)"))
        key_row = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("sk-proj-...")
        self.btn_show_key = QPushButton("👁️ Show")
        self.btn_show_key.setFixedWidth(70)
        self.btn_show_key.clicked.connect(self._toggle_key_visibility)
        key_row.addWidget(self.api_key_input, 1)
        key_row.addWidget(self.btn_show_key)
        ai_layout.addLayout(key_row)

        ai_layout.addWidget(QLabel("OPENAI MODEL"))
        self.openai_model_input = QLineEdit()
        self.openai_model_input.setText(config.openai_model)
        ai_layout.addWidget(self.openai_model_input)

        ai_layout.addWidget(QLabel("LOCAL AI ENDPOINT (Ollama / Local LLM)"))
        self.local_endpoint_input = QLineEdit()
        self.local_endpoint_input.setPlaceholderText("http://localhost:11434/v1")
        ai_layout.addWidget(self.local_endpoint_input)

        ai_layout.addStretch()
        tabs.addTab(tab_ai, "AI BRAIN")

        # Tab 2: Speech & Hardware
        tab_speech = QWidget()
        speech_layout = QVBoxLayout(tab_speech)
        speech_layout.setSpacing(10)

        speech_layout.addWidget(QLabel("MICROPHONE INPUT DEVICE"))
        self.mic_combo = QComboBox()
        self._populate_audio_devices()
        speech_layout.addWidget(self.mic_combo)

        speech_layout.addWidget(QLabel("WHISPER STT MODEL SIZE"))
        self.whisper_combo = QComboBox()
        self.whisper_combo.addItems(["tiny", "base", "small", "medium"])
        speech_layout.addWidget(self.whisper_combo)

        speech_layout.addWidget(QLabel("WAKE-WORD PHRASE"))
        self.wake_phrase_input = QLineEdit()
        self.wake_phrase_input.setText(config.wake_phrase)
        speech_layout.addWidget(self.wake_phrase_input)

        # Speech Rate
        rate_row = QHBoxLayout()
        self.rate_label = QLabel(f"SPEECH RATE: {config.speech_rate} WPM")
        rate_row.addWidget(self.rate_label)
        rate_row.addStretch()
        speech_layout.addLayout(rate_row)

        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setRange(100, 250)
        self.rate_slider.setValue(config.speech_rate)
        self.rate_slider.valueChanged.connect(
            lambda v: self.rate_label.setText(f"SPEECH RATE: {v} WPM")
        )
        speech_layout.addWidget(self.rate_slider)

        # Speech Volume
        vol_row = QHBoxLayout()
        vol_pct = int(config.speech_volume * 100)
        self.vol_label = QLabel(f"SPEECH VOLUME: {vol_pct}%")
        vol_row.addWidget(self.vol_label)
        vol_row.addStretch()
        speech_layout.addLayout(vol_row)

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(10, 100)
        self.vol_slider.setValue(vol_pct)
        self.vol_slider.valueChanged.connect(
            lambda v: self.vol_label.setText(f"SPEECH VOLUME: {v}%")
        )
        speech_layout.addWidget(self.vol_slider)

        # Test Voice Button
        btn_test_speech = QPushButton("🔊 Test Voice Synthesis")
        btn_test_speech.clicked.connect(self._test_voice)
        speech_layout.addWidget(btn_test_speech)

        speech_layout.addStretch()
        tabs.addTab(tab_speech, "SPEECH & AUDIO")

        # Tab 3: Languages
        tab_lang = QWidget()
        lang_layout = QVBoxLayout(tab_lang)
        lang_layout.setSpacing(10)

        lang_layout.addWidget(QLabel("DEFAULT APPLICATION LANGUAGE"))
        self.default_lang_combo = QComboBox()
        for spec in language_registry.all_languages():
            self.default_lang_combo.addItem(f"{spec.display_name} ({spec.code})", spec.code)
        lang_layout.addWidget(self.default_lang_combo)

        lang_layout.addWidget(QLabel("PREFERRED RESPONSE LANGUAGE POLICY"))
        self.pref_lang_combo = QComboBox()
        self.pref_lang_combo.addItem("Auto Detect (Mirrors User Language)", "auto")
        for spec in language_registry.all_languages():
            self.pref_lang_combo.addItem(f"{spec.display_name} ({spec.code})", spec.code)
        lang_layout.addWidget(self.pref_lang_combo)

        lang_layout.addStretch()
        tabs.addTab(tab_lang, "LANGUAGES")

        main_layout.addWidget(tabs, 1)

        # Bottom Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("CANCEL")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("SAVE CONFIGURATION")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self._save_settings)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        main_layout.addLayout(btn_row)

    def _populate_audio_devices(self):
        self.mic_combo.clear()
        self.mic_combo.addItem("System Default Recording Device", None)
        try:
            devices = AudioInputService.get_input_devices()
            for dev in devices:
                label = f"[{dev.index}] {dev.name}"
                if dev.is_default:
                    label += " (Default)"
                self.mic_combo.addItem(label, dev.index)
        except Exception as exc:
            logger.warning(f"Could not enumerate microphones: {exc}")

    def _toggle_key_visibility(self):
        if self.api_key_input.echoMode() == QLineEdit.Password:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
            self.btn_show_key.setText("🙈 Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
            self.btn_show_key.setText("👁️ Show")

    def _load_current_settings(self):
        # AI Mode
        saved_ai = self.memory.get_setting("ai_mode") or config.ai_mode
        idx = self.ai_mode_combo.findText(saved_ai)
        if idx >= 0:
            self.ai_mode_combo.setCurrentIndex(idx)

        # API Key
        saved_key = self.memory.get_setting("openai_api_key") or config.openai_api_key
        self.api_key_input.setText(saved_key)

        # Local endpoint
        saved_end = self.memory.get_setting("local_ai_endpoint") or config.local_ai_endpoint
        self.local_endpoint_input.setText(saved_end)

        # Whisper model
        saved_w = self.memory.get_setting("whisper_model_size") or config.whisper_model_size
        idx = self.whisper_combo.findText(saved_w)
        if idx >= 0:
            self.whisper_combo.setCurrentIndex(idx)

        # Default language
        saved_dl = self.memory.get_setting("default_language") or config.default_language
        for i in range(self.default_lang_combo.count()):
            if self.default_lang_combo.itemData(i) == saved_dl:
                self.default_lang_combo.setCurrentIndex(i)
                break

        # Preferred response language
        saved_pl = self.memory.get_setting("preferred_response_language") or config.preferred_response_language
        for i in range(self.pref_lang_combo.count()):
            if self.pref_lang_combo.itemData(i) == saved_pl:
                self.pref_lang_combo.setCurrentIndex(i)
                break

        # Speech rate & volume
        saved_rate = self.memory.get_setting("speech_rate")
        if saved_rate:
            try:
                self.rate_slider.setValue(int(saved_rate))
            except ValueError:
                pass

        saved_vol = self.memory.get_setting("speech_volume")
        if saved_vol:
            try:
                self.vol_slider.setValue(int(float(saved_vol) * 100))
            except ValueError:
                pass

    def _test_voice(self):
        if self.tts:
            rate = self.rate_slider.value()
            vol = float(self.vol_slider.value()) / 100.0
            self.tts.speak(
                text="Systems nominal. Voice synthesis test completed successfully.",
                language_code="en",
                rate=rate,
                volume=vol,
            )

    def _save_settings(self):
        # Update config & DB
        ai_mode = self.ai_mode_combo.currentText()
        api_key = self.api_key_input.text().strip()
        openai_model = self.openai_model_input.text().strip()
        local_endpoint = self.local_endpoint_input.text().strip()
        whisper_model = self.whisper_combo.currentText()
        wake_phrase = self.wake_phrase_input.text().strip().lower()
        mic_idx = self.mic_combo.currentData()
        rate = self.rate_slider.value()
        volume = float(self.vol_slider.value()) / 100.0
        default_lang = self.default_lang_combo.currentData()
        pref_lang = self.pref_lang_combo.currentData()

        # Update runtime config
        config.ai_mode = ai_mode
        config.openai_api_key = api_key
        config.openai_model = openai_model
        config.local_ai_endpoint = local_endpoint
        config.whisper_model_size = whisper_model
        config.wake_phrase = wake_phrase
        config.mic_device_index = mic_idx
        config.speech_rate = rate
        config.speech_volume = volume
        config.default_language = default_lang
        config.preferred_response_language = pref_lang

        # Persist to SQLite
        self.memory.set_setting("ai_mode", ai_mode)
        self.memory.set_setting("openai_api_key", api_key)
        self.memory.set_setting("openai_model", openai_model)
        self.memory.set_setting("local_ai_endpoint", local_endpoint)
        self.memory.set_setting("whisper_model_size", whisper_model)
        self.memory.set_setting("wake_phrase", wake_phrase)
        self.memory.set_setting("speech_rate", str(rate))
        self.memory.set_setting("speech_volume", str(volume))
        self.memory.set_setting("default_language", default_lang)
        self.memory.set_setting("preferred_response_language", pref_lang)

        logger.info("Saved and applied updated JARVIS configuration.")
        self.settings_updated.emit()
        self.accept()
