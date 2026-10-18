import os
from jarvis.config import JarvisConfig


def test_default_config():
    cfg = JarvisConfig()
    assert cfg.app_name == "J.A.R.V.I.S."
    assert cfg.wake_phrase == "hey jarvis"
    assert "notepad" in cfg.approved_apps
    assert "calculator" in cfg.approved_apps
    assert "https://www.google.com" in cfg.approved_websites


def test_custom_env_override(monkeypatch):
    monkeypatch.setenv("JARVIS_WAKE_PHRASE", "activate jarvis")
    monkeypatch.setenv("JARVIS_WHISPER_MODEL", "small")
    cfg = JarvisConfig()
    assert cfg.wake_phrase == "activate jarvis"
    assert cfg.whisper_model_size == "small"
