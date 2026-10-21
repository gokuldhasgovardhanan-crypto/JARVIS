import tempfile
import gc
from pathlib import Path
import pytest
from jarvis.memory.database import DatabaseManager
from jarvis.memory.repository import MemoryRepository
from jarvis.automation.permissions import PermissionGate
from jarvis.automation.windows_actions import WindowsActionRunner
from jarvis.core.intent_router import IntentRouter


@pytest.fixture
def test_setup():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db = DatabaseManager(Path(tmpdir) / "test_wa.db")
        repo = MemoryRepository(db)
        actions = WindowsActionRunner(repo)
        router = IntentRouter(repo, actions)
        yield repo, actions, router
        gc.collect()


def test_permission_gate_dynamic_resolution():
    # Built-in app
    allowed, target = PermissionGate.is_app_allowed("notepad")
    assert allowed is True
    assert "notepad" in target.lower()

    # WhatsApp UWP protocol
    allowed, target = PermissionGate.is_app_allowed("whatsapp")
    assert allowed is True
    assert "whatsapp" in target.lower()

    # Dynamic system app from registry (e.g. Chrome, Brave, Code)
    allowed, target = PermissionGate.is_app_allowed("chrome")
    assert allowed is True
    assert "chrome" in target.lower()


def test_whatsapp_message_routing_english(test_setup):
    repo, actions, router = test_setup
    res = router.route("send whatsapp message to John saying Hello, how are you?")
    assert res is not None
    assert res.intent == "whatsapp_send_message"
    assert "John" in res.message
    assert res.data["contact"] == "John"
    assert "Hello, how are you?" in res.data["text"]


def test_whatsapp_message_routing_phone_number(test_setup):
    repo, actions, router = test_setup
    res = router.route("send whatsapp message to +919876543210: Meeting confirmed at 4 PM")
    assert res is not None
    assert res.intent == "whatsapp_send_message"
    assert "919876543210" in res.data["contact"]
    assert "Meeting confirmed" in res.data["text"]


def test_whatsapp_message_routing_tamil(test_setup):
    repo, actions, router = test_setup
    res = router.route("whatsapp-la Suresh-ku Kalai vanakkam anupu")
    assert res is not None
    assert res.intent == "whatsapp_send_message"
    assert "Suresh" in res.data["contact"]
    assert "Kalai vanakkam" in res.data["text"]


def test_whatsapp_message_routing_hindi(test_setup):
    repo, actions, router = test_setup
    res = router.route("whatsapp par Rahul ko Namaste bhejo")
    assert res is not None
    assert res.intent == "whatsapp_send_message"
    assert "Rahul" in res.data["contact"]
    assert "Namaste" in res.data["text"]


def test_open_whatsapp_intent(test_setup):
    repo, actions, router = test_setup
    res = router.route("open whatsapp")
    assert res is not None
    assert "whatsapp" in res.intent.lower()


def test_take_screenshot_intent(test_setup):
    repo, actions, router = test_setup
    res = router.route("take screenshot")
    assert res is not None
    assert res.intent == "take_screenshot"


def test_dynamic_website_open(test_setup):
    repo, actions, router = test_setup
    res = router.route("open youtube")
    assert res is not None
    assert res.intent in ["open_youtube", "open_website"]
