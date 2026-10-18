import tempfile
import gc
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from jarvis.memory.database import DatabaseManager
from jarvis.memory.repository import MemoryRepository
from jarvis.core.assistant import JarvisAssistant


@pytest.fixture
def assistant():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_mgr = DatabaseManager(Path(tmpdir) / "test.db")
        repo = MemoryRepository(db_mgr)
        ast = JarvisAssistant(repo)
        yield ast
        gc.collect()


def test_multilingual_mixed_language_app_launch(assistant):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock()

        # Tamil-English mixed utterance
        res_ta = assistant.handle("notepad open pannu")
        assert "Opening notepad" in res_ta.text

        # Hindi-English mixed utterance
        res_hi = assistant.handle("calculator kholo")
        assert "Opening calculator" in res_hi.text

        # Telugu-English mixed utterance
        res_te = assistant.handle("notepad open cheyi")
        assert "Opening notepad" in res_te.text

        # German command
        res_de = assistant.handle("öffne notepad")
        assert "Opening notepad" in res_de.text


def test_windows_folder_and_search(assistant):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock()

        # Open downloads folder via English
        res_dl = assistant.handle("open downloads folder")
        assert "Opening Downloads folder" in res_dl.text or "Opened Downloads folder" in res_dl.text

        # Open desktop via Tanglish
        res_desk = assistant.handle("desktop open pannu")
        assert "desktop" in res_desk.text.lower()

    # Search files
    res_search = assistant.handle("search file config")
    assert "Found" in res_search.text or "matching" in res_search.text


def test_volume_and_media_controls(assistant):
    with patch("ctypes.windll.user32.keybd_event"):
        # Volume Up via English
        res_vol_up = assistant.handle("volume up")
        assert "Increased system volume" in res_vol_up.text

        # Volume Down via Tamil
        res_vol_down = assistant.handle("volume kora")
        assert "Decreased system volume" in res_vol_down.text

        # Volume Up via Hindi
        res_vol_hi = assistant.handle("volume badhao")
        assert "Increased system volume" in res_vol_hi.text

        # Volume Mute
        res_mute = assistant.handle("mute volume")
        assert "Toggled master volume mute" in res_mute.text

        # Media Play / Pause
        res_play = assistant.handle("play music")
        assert "Toggled media play/pause" in res_play.text

        # Media Next Track
        res_next = assistant.handle("next song")
        assert "Skipped to next track" in res_next.text


def test_system_vitals_telemetry(assistant):
    # Query system health
    res = assistant.handle("system vitals")
    assert "JARVIS System Vitals" in res.text
    assert "CPU Load" in res.text
    assert "RAM" in res.text
    assert "Disk" in res.text

    # Tanglish query
    res_ta = assistant.handle("laptop charge evlo")
    assert "JARVIS System Vitals" in res_ta.text


def test_sensitive_shutdown_and_restart_confirmation(assistant):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock()

        # Request shutdown -> Requires confirmation
        res_shut = assistant.handle("shutdown computer")
        assert res_shut.requires_confirmation is True
        assert "shut down" in res_shut.confirmation_prompt.lower()

        # Decline -> Operation canceled
        res_cancel = assistant.handle("no")
        assert "canceled" in res_cancel.text.lower()
        mock_popen.assert_not_called()

        # Request restart -> Requires confirmation
        res_restart = assistant.handle("restart computer")
        assert res_restart.requires_confirmation is True
        assert "restart" in res_restart.confirmation_prompt.lower()

        # Confirm -> Sequence initiated
        res_confirm = assistant.handle("yes")
        assert "initiated" in res_confirm.text.lower()
        mock_popen.assert_called_once()
