import tempfile
import gc
from pathlib import Path
import pytest
from jarvis.memory.database import DatabaseManager
from jarvis.memory.repository import MemoryRepository


@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"
        db_mgr = DatabaseManager(db_path)
        repo = MemoryRepository(db_mgr)
        yield repo
        gc.collect()


def test_notes_crud(temp_repo):
    # 1. Create
    n1_id = temp_repo.save_note("Remember to buy milk", tags="groceries")
    n2_id = temp_repo.save_note("Meeting with project team at 3 PM")
    assert n1_id > 0
    assert n2_id > n1_id

    # 2. Read
    notes = temp_repo.get_notes()
    assert len(notes) == 2
    assert notes[0]["id"] == n2_id
    assert notes[0]["note"] == "Meeting with project team at 3 PM"

    # 3. Search
    search_res = temp_repo.search_notes("milk")
    assert len(search_res) == 1
    assert search_res[0]["id"] == n1_id

    # 4. Delete
    deleted = temp_repo.delete_note(n1_id)
    assert deleted is True
    assert len(temp_repo.get_notes()) == 1

    # 5. Clear all
    cleared = temp_repo.clear_all_notes()
    assert cleared == 1
    assert len(temp_repo.get_notes()) == 0


def test_conversation_history(temp_repo):
    session = "test-session-123"
    temp_repo.add_conversation_turn(session, "user", "Hello Jarvis", "en", "en")
    temp_repo.add_conversation_turn(session, "assistant", "Hello! How can I help you?", "en", "en")

    history = temp_repo.get_conversation_history(session)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello Jarvis"
    assert history[1]["role"] == "assistant"

    # Clear history
    temp_repo.clear_conversation_history(session)
    assert len(temp_repo.get_conversation_history(session)) == 0


def test_settings_storage(temp_repo):
    temp_repo.set_setting("theme", "cyber_dark")
    assert temp_repo.get_setting("theme") == "cyber_dark"

    # Update setting
    temp_repo.set_setting("theme", "electric_blue")
    assert temp_repo.get_setting("theme") == "electric_blue"

    # Default fallback
    assert temp_repo.get_setting("non_existent", "default_val") == "default_val"


def test_audit_logging(temp_repo):
    log_id = temp_repo.log_action("launch_app", "notepad.exe", "success", "Launched Notepad")
    assert log_id > 0
    logs = temp_repo.get_recent_audit_logs()
    assert len(logs) >= 1
    assert logs[0]["action_type"] == "launch_app"
    assert logs[0]["status"] == "success"
