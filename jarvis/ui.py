from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QLineEdit, QPushButton, QFrame
)

from .assistant import JarvisAssistant
from .voice import VoiceEngine


STYLE = """
QMainWindow, QWidget { background: #07111f; color: #d8f7ff; }
QLabel#eyebrow { color: #4deaff; letter-spacing: 3px; font-size: 11px; }
QLabel#title { color: #e9fbff; font-size: 30px; font-weight: 700; }
QLabel#status { color: #63ddec; font-size: 12px; }
QFrame#panel { background: #0b1b2b; border: 1px solid #17475a; border-radius: 14px; }
QTextEdit { background: #081522; border: 1px solid #14394b; border-radius: 10px; padding: 12px; color: #d8f7ff; font-size: 13px; }
QLineEdit { background: #081522; border: 1px solid #1c596c; border-radius: 10px; padding: 12px; color: #e9fbff; }
QPushButton { background: #0d3447; color: #a9f6ff; border: 1px solid #24788b; border-radius: 9px; padding: 10px 14px; font-weight: 600; }
QPushButton:hover { background: #14516a; }
QPushButton#primary { background: #087f99; color: white; }
QPushButton#danger { background: #38202a; border-color: #824050; color: #ffc8d1; }
"""


class UiSignals(QObject):
    status = Signal(str)
    error = Signal(str)
    command = Signal(str)


class JarvisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S. — Personal AI")
        self.resize(1040, 720)
        self.assistant = JarvisAssistant()
        self.signals = UiSignals()
        self.signals.status.connect(self.set_status)
        self.signals.error.connect(self.show_error)
        self.signals.command.connect(self.handle_voice_command)
        self.voice = VoiceEngine(
            on_status=self.signals.status.emit,
            on_command=self.signals.command.emit,
            on_error=self.signals.error.emit,
        )
        self._build_ui()
        self.add_message("JARVIS", "Systems online. Type a command, or enable voice activation and say “Hey Jarvis”.")
        self.set_status("LOCAL SYSTEM READY  •  AI " + ("CONNECTED" if self.assistant.client else "NOT CONFIGURED"))

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        top = QHBoxLayout()
        labels = QVBoxLayout()
        eyebrow = QLabel("PERSONAL ARTIFICIAL INTELLIGENCE")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("J.A.R.V.I.S.")
        title.setObjectName("title")
        subtitle = QLabel("DESKTOP INTELLIGENCE  /  WINDOWS 11")
        subtitle.setStyleSheet("color:#7297a7; font-size:11px; letter-spacing:2px;")
        labels.addWidget(eyebrow)
        labels.addWidget(title)
        labels.addWidget(subtitle)
        top.addLayout(labels)
        top.addStretch()
        self.status = QLabel("INITIALIZING")
        self.status.setObjectName("status")
        self.status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top.addWidget(self.status)
        layout.addLayout(top)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.addWidget(QLabel("COMMAND CONSOLE"))
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setMinimumHeight(400)
        panel_layout.addWidget(self.chat)
        layout.addWidget(panel, 1)

        input_row = QHBoxLayout()
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Tell JARVIS what you need…")
        self.entry.returnPressed.connect(self.send_text)
        send_btn = QPushButton("SEND")
        send_btn.setObjectName("primary")
        send_btn.clicked.connect(self.send_text)
        input_row.addWidget(self.entry, 1)
        input_row.addWidget(send_btn)
        layout.addLayout(input_row)

        buttons = QHBoxLayout()
        self.listen_btn = QPushButton("ENABLE “HEY JARVIS”")
        self.listen_btn.clicked.connect(self.start_voice)
        stop_btn = QPushButton("STOP LISTENING")
        stop_btn.setObjectName("danger")
        stop_btn.clicked.connect(self.voice.stop)
        help_btn = QPushButton("COMMANDS")
        help_btn.clicked.connect(lambda: self.add_message("JARVIS", self.assistant.handle("help")))
        buttons.addWidget(self.listen_btn)
        buttons.addWidget(stop_btn)
        buttons.addStretch()
        buttons.addWidget(help_btn)
        layout.addLayout(buttons)

    def set_status(self, message):
        self.status.setText(message.upper())

    def show_error(self, message):
        self.add_message("SYSTEM", message)

    def add_message(self, who, message):
        safe = (message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        color = "#4deaff" if who == "JARVIS" else ("#ffb7c5" if who == "SYSTEM" else "#b4c9d5")
        self.chat.append(f'<p style="margin:8px 0 3px;color:{color};"><b>{who}</b></p><p style="margin:0 0 12px;color:#d8f7ff;">{safe}</p>')

    def send_text(self):
        text = self.entry.text().strip()
        if not text:
            return
        self.entry.clear()
        self.add_message("YOU", text)
        self.set_status("PROCESSING")
        answer = self.assistant.handle(text)
        self.add_message("JARVIS", answer)
        self.set_status("READY")
        self.voice.speak(answer)

    def handle_voice_command(self, command):
        self.add_message("YOU (VOICE)", command)
        self.set_status("PROCESSING VOICE COMMAND")
        answer = self.assistant.handle(command)
        self.add_message("JARVIS", answer)
        self.set_status("VOICE ACTIVE")
        self.voice.speak(answer)

    def start_voice(self):
        self.voice.start_wake_listener()
        self.set_status("STARTING MICROPHONE")
        self.listen_btn.setText("VOICE LISTENER ENABLED")

    def closeEvent(self, event):
        self.voice.stop()
        event.accept()
