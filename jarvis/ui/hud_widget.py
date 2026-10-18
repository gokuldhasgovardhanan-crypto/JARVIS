import math
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QRadialGradient,
    QConicalGradient,
    QFont,
)
from PySide6.QtWidgets import QWidget


class JarvisHudWidget(QWidget):
    """
    Futuristic HUD / Arc Reactor widget with dynamic animations for:
    READY, LISTENING, PROCESSING, SPEAKING, and ERROR states.
    """

    STATE_COLORS = {
        "READY": (QColor("#00e5ff"), QColor("#007799")),
        "LISTENING": (QColor("#00ffff"), QColor("#00aaff")),
        "PROCESSING": (QColor("#38ef7d"), QColor("#11998e")),
        "SPEAKING": (QColor("#00f2fe"), QColor("#4facfe")),
        "ERROR": (QColor("#ff416c"), QColor("#ff4b2b")),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 180)
        self.state = "READY"
        self.rotation_angle = 0.0
        self.pulse_phase = 0.0
        self.audio_level = 0.0  # 0.0 to 1.0

        # Animation timer (40 FPS for smooth cyber visuals)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(25)

    def set_state(self, state: str) -> None:
        """Updates the active visual HUD state."""
        clean_state = state.upper()
        if clean_state in self.STATE_COLORS:
            self.state = clean_state
        else:
            self.state = "READY"
        self.update()

    def set_audio_level(self, level: float) -> None:
        """Sets normalized audio volume level (0.0 to 1.0) for waveform visualization."""
        self.audio_level = max(0.0, min(1.0, level))
        self.update()

    def _tick(self) -> None:
        # Rotation speed depends on state
        speed = 2.5 if self.state == "PROCESSING" else (1.5 if self.state == "LISTENING" else 0.8)
        self.rotation_angle = (self.rotation_angle + speed) % 360.0

        # Pulse oscillation
        pulse_speed = 0.12 if self.state == "SPEAKING" else (0.08 if self.state == "LISTENING" else 0.04)
        self.pulse_phase = (self.pulse_phase + pulse_speed) % (2 * math.pi)

        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        center_x = w / 2.0
        center_y = h / 2.0
        radius = min(w, h) / 2.0 - 14.0

        primary_color, secondary_color = self.STATE_COLORS.get(self.state, self.STATE_COLORS["READY"])

        # Pulse multiplier
        pulse = (math.sin(self.pulse_phase) + 1.0) / 2.0  # 0.0 to 1.0
        effective_radius = radius * (0.92 + 0.08 * pulse)

        # 1. Background radial aura
        aura = QRadialGradient(center_x, center_y, effective_radius * 1.2)
        glow_alpha = int(35 + 40 * pulse) if self.state in {"LISTENING", "SPEAKING", "PROCESSING"} else 25
        c_glow = QColor(primary_color)
        c_glow.setAlpha(glow_alpha)
        aura.setColorAt(0.0, c_glow)
        aura.setColorAt(0.7, QColor(primary_color.red(), primary_color.green(), primary_color.blue(), int(glow_alpha / 3)))
        aura.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(aura))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - effective_radius * 1.2, center_y - effective_radius * 1.2, effective_radius * 2.4, effective_radius * 2.4)

        # 2. Outer decorative track ring
        outer_pen = QPen(QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 50), 1.5)
        painter.setPen(outer_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2.0, radius * 2.0)

        # 3. Rotating outer segmented cyber arcs
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.rotation_angle)

        arc_pen = QPen(primary_color, 2.5)
        arc_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(arc_pen)

        rect_outer = QRectF(-radius, -radius, radius * 2.0, radius * 2.0)
        # 3 Segmented arcs with gaps
        painter.drawArc(rect_outer, 0 * 16, 70 * 16)
        painter.drawArc(rect_outer, 120 * 16, 70 * 16)
        painter.drawArc(rect_outer, 240 * 16, 70 * 16)

        # Reverse inner rotating dashed ring
        painter.rotate(-self.rotation_angle * 2.0)
        inner_r = radius * 0.76
        rect_inner = QRectF(-inner_r, -inner_r, inner_r * 2.0, inner_r * 2.0)
        inner_pen = QPen(secondary_color, 1.8, Qt.DashLine)
        painter.setPen(inner_pen)
        painter.drawEllipse(rect_inner)

        painter.restore()

        # 4. Central Glowing Arc Reactor Core
        core_r = radius * (0.38 + 0.08 * pulse)
        if self.state == "SPEAKING":
            core_r += self.audio_level * radius * 0.2

        core_grad = QRadialGradient(center_x, center_y, core_r)
        core_grad.setColorAt(0.0, QColor(255, 255, 255, 240))
        core_grad.setColorAt(0.4, primary_color)
        c_outer = QColor(secondary_color)
        c_outer.setAlpha(120)
        core_grad.setColorAt(1.0, c_outer)

        painter.setPen(QPen(primary_color, 2.0))
        painter.setBrush(QBrush(core_grad))
        painter.drawEllipse(center_x - core_r, center_y - core_r, core_r * 2.0, core_r * 2.0)

        # 5. Core state text
        painter.setPen(QColor("#041018"))
        font = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font)
        text_rect = QRectF(center_x - core_r, center_y - core_r, core_r * 2.0, core_r * 2.0)
        painter.drawText(text_rect, Qt.AlignCenter, self.state)
