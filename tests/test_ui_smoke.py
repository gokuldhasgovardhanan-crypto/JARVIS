import os
import pytest
from PySide6.QtWidgets import QApplication
from jarvis.ui.main_window import JarvisWindow


@pytest.fixture(scope="session")
def qapp():
    # Use offscreen platform for reliable headless CI / test execution
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_main_window_initialization(qapp):
    window = JarvisWindow()
    assert window.windowTitle() == "J.A.R.V.I.S. — Personal AI Assistant"
    assert window.hud is not None
    assert window.memory_panel is not None
    assert window.chat_console is not None
    assert window.command_input is not None

    # Test executing a command through UI
    window.execute_command_text("what time is it")
    text = window.chat_console.toPlainText()
    assert "The current time is" in text

    # Test diagnostics button
    window._run_diagnostics()
    text = window.chat_console.toPlainText()
    assert "JARVIS System Diagnostics" in text

    window.show()
    # Test memory panel toggle
    assert window.memory_panel.isVisible() is True
    window._toggle_memory_panel()
    assert window.memory_panel.isVisible() is False
    window._toggle_memory_panel()
    assert window.memory_panel.isVisible() is True

    # Test HUD 40 FPS timer is initialized and running
    assert window.hud.timer is not None
    assert window.hud.timer.isActive() is True
    assert window.hud.timer.interval() == 25  # 40 FPS (1000ms / 40 = 25ms)

    # Test level updates to HUD
    window._on_level_received(0.75)
    assert window.hud.audio_level == 0.75

    # Test settings dialog smoke
    assert hasattr(window, "_open_settings_dialog")

    window.close()


