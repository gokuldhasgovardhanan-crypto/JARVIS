import threading
from typing import Optional
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QFrame,
    QComboBox,
    QSplitter,
    QMessageBox,
)

from jarvis.core.assistant import JarvisAssistant, AssistantResponse
from jarvis.ui.hud_widget import JarvisHudWidget
from jarvis.ui.memory_panel import MemoryPanel
from jarvis.voice.audio_input import AudioInputService
from jarvis.voice.speech_recognition import STTManager, TranscriptionResult
from jarvis.voice.speech_synthesis import TTSManager
from jarvis.voice.wake_word import WakeWordEngine
from jarvis.languages.registry import language_registry
from jarvis.ui.settings_dialog import SettingsDialog

from jarvis.config import config
from jarvis.utils.logging_config import logger


HUD_STYLE = """
QMainWindow, QWidget {
    background-color: #050d17;
    color: #d8f7ff;
    font-family: 'Segoe UI', -apple-system, sans-serif;
}
QLabel#eyebrow {
    color: #38c8e8;
    letter-spacing: 3px;
    font-size: 10px;
    font-weight: 600;
}
QLabel#title {
    color: #e9fbff;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 1px;
}
QLabel#status_badge {
    background-color: #072233;
    border: 1px solid #144f66;
    border-radius: 4px;
    padding: 4px 10px;
    color: #00e5ff;
    font-size: 11px;
    font-weight: 600;
}
QFrame#panel {
    background-color: #081624;
    border: 1px solid #10384a;
    border-radius: 12px;
}
QTextEdit#chat_console {
    background-color: #040c14;
    border: 1px solid #0f2e3d;
    border-radius: 8px;
    padding: 14px;
    color: #d8f7ff;
    font-size: 13px;
    line-height: 1.4;
}
QLineEdit#command_input {
    background-color: #071929;
    border: 1px solid #1c596c;
    border-radius: 8px;
    padding: 12px 16px;
    color: #e9fbff;
    font-size: 13px;
}
QLineEdit#command_input:focus {
    border: 1px solid #00e5ff;
    background-color: #092136;
}
QPushButton {
    background-color: #09283b;
    color: #a9f6ff;
    border: 1px solid #195b73;
    border-radius: 8px;
    padding: 9px 15px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #12405c;
    border-color: #00e5ff;
}
QPushButton#primary {
    background-color: #007799;
    color: #ffffff;
    border: 1px solid #00c8e6;
}
QPushButton#primary:hover {
    background-color: #0099bf;
}
QPushButton#ptt_active {
    background-color: #00b4d8;
    color: #02121e;
    font-weight: bold;
    border: 1px solid #90e0ef;
}
QPushButton#danger {
    background-color: #38202a;
    border: 1px solid #824050;
    color: #ffc8d1;
}
QPushButton#danger:hover {
    background-color: #592534;
}
QPushButton#chip {
    background-color: #071f30;
    border: 1px solid #13465b;
    border-radius: 14px;
    padding: 4px 12px;
    font-size: 11px;
    color: #72cbe6;
}
QPushButton#chip:hover {
    background-color: #0e374f;
    color: #00e5ff;
}
QComboBox {
    background-color: #092538;
    border: 1px solid #195b73;
    border-radius: 6px;
    padding: 5px 10px;
    color: #4deaff;
    font-size: 11px;
}
"""


class VoiceBridgeSignals(QObject):
    """Thread-safe signals bridging background audio workers to Qt UI."""
    level = Signal(float)
    transcription_ready = Signal(str, str)
    wake_word_detected = Signal()
    status_msg = Signal(str)
    speech_done = Signal()
    error = Signal(str)


class JarvisWindow(QMainWindow):
    """Futuristic Desktop Interface for Personal JARVIS with full speech I/O."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S. — Personal AI Assistant")
        self.resize(1180, 780)
        self.setStyleSheet(HUD_STYLE)

        self.assistant = JarvisAssistant()
        self.stt = STTManager()
        self.tts = TTSManager()

        # Audio buffer for microphone capture
        self._audio_buffer = bytearray()
        self._is_recording = False

        # Signals
        self.signals = VoiceBridgeSignals()
        self.signals.level.connect(self._on_level_received)
        self.signals.transcription_ready.connect(self._on_transcription_ready)
        self.signals.wake_word_detected.connect(self._on_wake_word_detected)
        self.signals.status_msg.connect(lambda msg: self.add_message("SYSTEM", msg, meta="WAKE WORD"))
        self.signals.speech_done.connect(self._on_speech_finished)
        self.signals.error.connect(self._on_voice_error)

        # Audio service for Push-to-Talk
        self.audio = AudioInputService(
            sample_rate=16000,
            on_level=lambda lvl: self.signals.level.emit(lvl),
            on_speech_chunk=self._on_raw_chunk,
            on_error=lambda err: self.signals.error.emit(err),
        )

        # Dedicated Wake-word engine for continuous "Hey Jarvis"
        self.wake_engine = WakeWordEngine(
            wake_phrase=config.wake_phrase,
            on_wake_detected=lambda: self.signals.wake_word_detected.emit(),
            on_level=lambda lvl: self.signals.level.emit(lvl),
            on_status=lambda s: self.signals.status_msg.emit(s),
            on_error=lambda err: self.signals.error.emit(err),
        )

        self._build_ui()


        # Display initial welcome message
        self.add_message(
            "JARVIS",
            "Core neural systems online. Speech input (Faster-Whisper), multi-tier language detection, "
            "and text-to-speech engine ready.<br>"
            "Type a command, use Push-to-Talk, or click quick actions below.",
            meta="SYSTEM BOOT"
        )
        self.set_hud_state("READY")

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # 1. Header Bar
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        eyebrow = QLabel("PERSONAL ARTIFICIAL INTELLIGENCE")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("J.A.R.V.I.S.")
        title.setObjectName("title")
        subtitle = QLabel("WINDOWS 11 MULTILINGUAL COMMAND CENTER")
        subtitle.setStyleSheet("color: #558ca0; font-size: 10px; letter-spacing: 1.5px;")
        title_box.addWidget(eyebrow)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        # Status Badges
        self.stt_badge = QLabel("STT: FASTER-WHISPER")
        self.stt_badge.setObjectName("status_badge")
        self.ai_badge = QLabel("AI: HYBRID")
        self.ai_badge.setObjectName("status_badge")
        self.lang_badge = QLabel("LANG: AUTO")
        self.lang_badge.setObjectName("status_badge")
        header.addWidget(self.stt_badge)
        header.addWidget(self.ai_badge)
        header.addWidget(self.lang_badge)

        main_layout.addLayout(header)

        # 2. Main Content Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left Column: HUD & Voice Controls
        left_panel = QFrame()
        left_panel.setObjectName("panel")
        left_panel.setFixedWidth(240)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(10)

        # Arc Reactor HUD Widget
        self.hud = JarvisHudWidget()
        left_layout.addWidget(self.hud, alignment=Qt.AlignCenter)

        # Response Language Selector
        left_layout.addWidget(QLabel("RESPONSE LANGUAGE"))
        self.lang_selector = QComboBox()
        self.lang_selector.addItems([
            "Auto Detect", "English (en)", "Tamil (ta)", "Hindi (hi)",
            "Telugu (te)", "Malayalam (ml)", "Kannada (kn)",
            "German (de)", "French (fr)", "Spanish (es)", "Japanese (ja)"
        ])
        left_layout.addWidget(self.lang_selector)

        left_layout.addSpacing(6)
        left_layout.addWidget(QLabel("VOICE CONTROLS"))

        # Continuous Wake-word Button
        self.wake_btn = QPushButton("ENABLE “HEY JARVIS”")
        self.wake_btn.setObjectName("chip")
        self.wake_btn.clicked.connect(self._toggle_wake_word)
        left_layout.addWidget(self.wake_btn)

        # PTT Button
        self.ptt_btn = QPushButton("🎤 START VOICE (PTT)")
        self.ptt_btn.setObjectName("primary")
        self.ptt_btn.clicked.connect(self._toggle_voice_recording)
        left_layout.addWidget(self.ptt_btn)


        # Stop Speaking Button
        self.stop_speech_btn = QPushButton("⏹️ STOP SPEAKING")
        self.stop_speech_btn.setObjectName("danger")
        self.stop_speech_btn.clicked.connect(self._stop_speaking)
        left_layout.addWidget(self.stop_speech_btn)

        # Voice Capabilities Button
        btn_voice_caps = QPushButton("VOICE CAPABILITIES")
        btn_voice_caps.clicked.connect(self._show_voice_capabilities)
        left_layout.addWidget(btn_voice_caps)

        # Diagnostics, Settings & Toggle Archive
        btn_diag = QPushButton("DIAGNOSTICS")
        btn_diag.clicked.connect(self._run_diagnostics)
        left_layout.addWidget(btn_diag)

        btn_settings = QPushButton("⚙️ SETTINGS")
        btn_settings.clicked.connect(self._open_settings_dialog)
        left_layout.addWidget(btn_settings)

        btn_notes = QPushButton("TOGGLE ARCHIVE")
        btn_notes.clicked.connect(self._toggle_memory_panel)
        left_layout.addWidget(btn_notes)

        btn_clear = QPushButton("CLEAR CONSOLE")
        btn_clear.clicked.connect(self.chat_console_clear)
        left_layout.addWidget(btn_clear)

        left_layout.addStretch()
        splitter.addWidget(left_panel)

        # Middle Column: Conversation Console & Command Input
        middle_panel = QFrame()
        middle_panel.setObjectName("panel")
        mid_layout = QVBoxLayout(middle_panel)
        mid_layout.setContentsMargins(14, 14, 14, 14)
        mid_layout.setSpacing(10)

        self.chat_console = QTextEdit()
        self.chat_console.setObjectName("chat_console")
        self.chat_console.setReadOnly(True)
        mid_layout.addWidget(self.chat_console, 1)

        # Chips row for quick commands
        chips_row = QHBoxLayout()
        chips = [
            ("Time", "what time is it"),
            ("Vitals", "system vitals"),
            ("Notepad", "open notepad"),
            ("Calculator", "open calculator"),
            ("Downloads", "open downloads folder"),
            ("Vol +", "volume up"),
            ("Vol -", "volume down"),
            ("Notes", "show my notes"),
            ("Help", "help"),
        ]
        for label, cmd_text in chips:
            chip_btn = QPushButton(label)
            chip_btn.setObjectName("chip")
            chip_btn.clicked.connect(lambda _, t=cmd_text: self.execute_command_text(t))
            chips_row.addWidget(chip_btn)
        chips_row.addStretch()
        mid_layout.addLayout(chips_row)

        # Input row
        input_row = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setObjectName("command_input")
        self.command_input.setPlaceholderText("Enter command or question (e.g. 'open notepad', 'translate Hello to German')...")
        self.command_input.returnPressed.connect(self.on_send_clicked)

        send_btn = QPushButton("EXECUTE")
        send_btn.setObjectName("primary")
        send_btn.clicked.connect(self.on_send_clicked)

        input_row.addWidget(self.command_input, 1)
        input_row.addWidget(send_btn)
        mid_layout.addLayout(input_row)

        splitter.addWidget(middle_panel)

        # Right Column: Memory Panel
        self.memory_panel = MemoryPanel(self.assistant.memory)
        self.memory_panel.setFixedWidth(320)
        self.memory_panel.note_changed.connect(self._on_memory_updated)
        splitter.addWidget(self.memory_panel)

        main_layout.addWidget(splitter, 1)

    def set_hud_state(self, state: str):
        self.hud.set_state(state)

    def add_message(self, who: str, message: str, meta: str = ""):
        color = "#00e5ff" if who == "JARVIS" else ("#ff6b8b" if who == "SYSTEM" else "#ffffff")
        meta_html = f"<span style='color: #4a778c; font-size: 10px; margin-left: 8px;'>[{meta}]</span>" if meta else ""
        formatted = (
            f"<div style='margin-bottom: 12px;'>"
            f"<span style='color: {color}; font-weight: bold; font-size: 11px;'>{who}</span>{meta_html}"
            f"<div style='margin-top: 3px; color: #d8f7ff; line-height: 1.4;'>{message.replace(chr(10), '<br>')}</div>"
            f"</div>"
        )
        self.chat_console.append(formatted)
        self.chat_console.verticalScrollBar().setValue(
            self.chat_console.verticalScrollBar().maximum()
        )

    def on_send_clicked(self):
        text = self.command_input.text().strip()
        if not text:
            return
        self.command_input.clear()
        self.execute_command_text(text)

    def execute_command_text(self, text: str, is_voice: bool = False):
        sender = "YOU (VOICE)" if is_voice else "YOU"
        self.add_message(sender, text)
        self.set_hud_state("PROCESSING")

        # Map selected response language
        lang_choice = self.lang_selector.currentText()
        pref_lang = None
        if "(" in lang_choice:
            pref_lang = lang_choice.split("(")[1].replace(")", "").strip()

        # Execute via Assistant with automatic language detection
        try:
            resp: AssistantResponse = self.assistant.handle(
                text,
                detected_language="auto",
                preferred_response_language=pref_lang,
            )

            # Update header badges
            self.lang_badge.setText(f"LANG: {resp.detected_language.upper()} → {resp.response_language.upper()}")
            self.ai_badge.setText(f"AI: {resp.provider_name.upper()}")

            if resp.requires_confirmation:
                self.set_hud_state("ERROR")
                self.add_message("JARVIS", f"⚠️ <b>CONFIRMATION REQUIRED:</b> {resp.text}", meta="SENSITIVE ACTION")
            else:
                self.set_hud_state("SPEAKING")
                meta_tag = f"{resp.provider_name} • {resp.response_language.upper()}"
                self.add_message("JARVIS", resp.text, meta=meta_tag)

                self.wake_engine.set_speaking_state(True)
                # Synthesize speech output in target language
                self.tts.speak(
                    text=resp.text,
                    language_code=resp.response_language,
                    on_done=lambda: self.signals.speech_done.emit(),
                )

            # Refresh memory panel if a note or setting was affected
            if resp.action_result and resp.action_result.intent in {"save_note", "clear_notes", "set_language"}:
                self.memory_panel.refresh()

        except Exception as exc:
            self.set_hud_state("ERROR")
            self.add_message("SYSTEM", f"Execution error: {exc}", meta="ERROR")
            logger.error(f"Command error: {exc}", exc_info=True)
            self.set_hud_state("READY")

    # --- Audio & Voice Handlers ---
    def _toggle_wake_word(self):
        """Toggles hands-free continuous wake-word listening."""
        if not self.wake_engine.is_running:
            if self._is_recording:
                self._toggle_voice_recording()
            started = self.wake_engine.start()
            if started:
                self.wake_btn.setText("DISABLE “HEY JARVIS”")
                self.wake_btn.setStyleSheet("background-color: #00e5ff; color: #040d12; font-weight: bold;")
                self.add_message("SYSTEM", "Continuous wake-word engine enabled. Say 'Hey Jarvis' to activate.", meta="WAKE ENGINE")
        else:
            self.wake_engine.stop()
            self.wake_btn.setText("ENABLE “HEY JARVIS”")
            self.wake_btn.setStyleSheet("")
            self.add_message("SYSTEM", "Wake-word engine paused.", meta="WAKE ENGINE")

    def _on_wake_word_detected(self):
        """Called on background thread via Qt signal when 'Hey Jarvis' is triggered."""
        self.set_hud_state("LISTENING")
        self.add_message("JARVIS", "Yes? I am listening...", meta="WAKE WORD")
        self._start_wake_command_recording()

    def _start_wake_command_recording(self):
        """Automatically begins recording the user's voice command after wake trigger."""
        if self._is_recording:
            return
        self.wake_engine.set_speaking_state(True)  # Suppress wake word while recording command
        self._toggle_voice_recording()
        # Automatically stop recording after 4.5 seconds to process command
        QTimer.singleShot(4500, self._auto_stop_wake_recording)

    def _auto_stop_wake_recording(self):
        """Automatically finishes recording for wake command and routes to transcription."""
        if self._is_recording:
            self._toggle_voice_recording()
            self.wake_engine.set_speaking_state(False)

    def _toggle_voice_recording(self):
        if not self._is_recording:
            # Start recording
            self._is_recording = True
            self._audio_buffer.clear()
            self.ptt_btn.setText("🔴 STOP RECORDING")
            self.ptt_btn.setStyleSheet("background-color: #e63946; color: white;")
            self.set_hud_state("LISTENING")
            self.audio.start_recording()
        else:
            # Stop recording and process
            self._is_recording = False
            self.ptt_btn.setText("🎤 START VOICE (PTT)")
            self.ptt_btn.setStyleSheet("")
            self.audio.stop_recording()
            self.set_hud_state("PROCESSING")

            raw_bytes = bytes(self._audio_buffer)
            self._audio_buffer.clear()

            if len(raw_bytes) < 3200:  # Less than 0.1s
                self.set_hud_state("READY")
                return

            def transcribe_worker():
                try:
                    result: TranscriptionResult = self.stt.transcribe(raw_bytes, sample_rate=16000)
                    self.signals.transcription_ready.emit(result.text, result.language)
                except Exception as exc:
                    self.signals.error.emit(f"Transcription error: {exc}")

            threading.Thread(target=transcribe_worker, daemon=True, name="STTWorker").start()

    def _on_raw_chunk(self, pcm_bytes: bytes):
        if self._is_recording:
            self._audio_buffer.extend(pcm_bytes)

    def _on_level_received(self, level: float):
        self.hud.set_audio_level(level)

    def _on_transcription_ready(self, text: str, detected_lang: str):
        if not text.strip():
            self.add_message("SYSTEM", "No speech recognized. Please speak clearly.", meta="VOICE RECOGNITION")
            self.set_hud_state("READY")
            return
        self.execute_command_text(text, is_voice=True)

    def _on_speech_finished(self):
        self.wake_engine.set_speaking_state(False)
        self.set_hud_state("READY")

    def _stop_speaking(self):
        self.tts.stop()
        self.wake_engine.set_speaking_state(False)
        self.set_hud_state("READY")
        self.add_message("SYSTEM", "Speech output stopped.", meta="AUDIO CONTROL")

    def _show_voice_capabilities(self):
        table = self.tts.get_capability_table()
        lines = ["<b>JARVIS Voice Synthesis Capabilities:</b><br>"]
        for code, info in table.items():
            loc_status = "✅ Local SAPI Voice" if info["local_voice_available"] else "❌ No Local Voice"
            cld_status = f"✅ Cloud ({info['cloud_voice_name']})" if info["cloud_voice_available"] else "❌ Cloud Disabled"
            lines.append(f"• <b>{info['display_name']} ({code})</b>: {loc_status} | {cld_status}")
        self.add_message("SYSTEM", "<br>".join(lines), meta="CAPABILITY AUDIT")

    def _on_voice_error(self, message: str):
        self.add_message("SYSTEM", message, meta="AUDIO ERROR")
        self.set_hud_state("READY")

    def _run_diagnostics(self):
        self.execute_command_text("diagnostics")

    def _toggle_memory_panel(self):
        self.memory_panel.setVisible(not self.memory_panel.isVisible())

    def _on_memory_updated(self):
        self.add_message("SYSTEM", "Local memory archive updated.", meta="DATABASE")

    def chat_console_clear(self):
        self.chat_console.clear()

    def _open_settings_dialog(self):
        dialog = SettingsDialog(self.assistant.memory, self.tts, parent=self)
        dialog.settings_updated.connect(self._on_settings_updated)
        dialog.exec()

    def _on_settings_updated(self):
        self.ai_badge.setText(f"AI: {config.ai_mode.upper()}")
        self.lang_badge.setText(f"LANG: {config.default_language.upper()} → {config.preferred_response_language.upper()}")
        self.add_message("SYSTEM", "System preferences updated and applied.", meta="SETTINGS")

    def closeEvent(self, event):
        self.wake_engine.stop()
        self.audio.stop_recording()
        self.tts.stop()
        event.accept()
