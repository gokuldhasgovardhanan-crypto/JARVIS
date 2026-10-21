import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

USER_DATA_DIR = Path.home() / "AppData" / "Local" / "PersonalJarvis"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = USER_DATA_DIR / "jarvis_memory.db"
LOGS_DIR = USER_DATA_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class JarvisConfig:
    app_name: str = "J.A.R.V.I.S."
    version: str = "1.0.0"
    
    # Audio & Wake-word
    wake_phrase: str = field(
        default_factory=lambda: os.getenv("JARVIS_WAKE_PHRASE", "hey jarvis").lower().strip()
    )
    speech_rate: int = 175
    speech_volume: float = 1.0
    mic_device_index: int | None = None
    
    # Multilingual & Speech Recognition
    default_language: str = "en"
    preferred_response_language: str = "auto"
    whisper_model_size: str = field(
        default_factory=lambda: os.getenv("JARVIS_WHISPER_MODEL", "base")
    )
    whisper_device: str = field(
        default_factory=lambda: os.getenv("JARVIS_WHISPER_DEVICE", "cpu")
    )
    
    # AI Provider
    openai_api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "").strip()
    )
    openai_model: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    )
    local_ai_endpoint: str = field(
        default_factory=lambda: os.getenv("JARVIS_LOCAL_AI_ENDPOINT", "http://localhost:11434/v1")
    )
    ai_mode: str = field(
        default_factory=lambda: os.getenv("JARVIS_AI_MODE", "hybrid")  # local, cloud, hybrid
    )
    
    # Safety & Allowlist
    approved_websites: List[str] = field(
        default_factory=lambda: [
            "https://www.google.com",
            "https://www.youtube.com",
            "https://github.com",
            "https://en.wikipedia.org",
            "https://weather.com",
            "https://reddit.com",
            "https://stackoverflow.com",
            "https://web.whatsapp.com",
            "https://mail.google.com",
            "https://netflix.com",
            "https://amazon.com",
            "https://twitter.com",
            "https://x.com",
            "https://instagram.com",
            "https://chat.openai.com",
        ]
    )
    approved_apps: dict[str, str] = field(
        default_factory=lambda: {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "paint": "mspaint.exe",
            "mspaint": "mspaint.exe",
            "task manager": "taskmgr.exe",
            "taskmgr": "taskmgr.exe",
            "terminal": "wt.exe",
            "control panel": "control.exe",
            # Messaging & Communication
            "whatsapp": "whatsapp:",
            "whatsapp desktop": "whatsapp:",
            "teams": "ms-teams:",
            "ms teams": "ms-teams:",
            "discord": "discord.exe",
            "telegram": "telegram.exe",
            # Browsers
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",
            "brave": "brave.exe",
            "brave browser": "brave.exe",
            "firefox": "firefox.exe",
            # Productivity & Development
            "code": "code.cmd",
            "vscode": "code.cmd",
            "vs code": "code.cmd",
            "word": "winword.exe",
            "winword": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "ppt": "powerpnt.exe",
            "onenote": "onenote.exe",
            "wps": "wps.exe",
            # Multimedia & Utilities
            "spotify": "spotify:",
            "vlc": "vlc.exe",
            "snipping tool": "snippingtool.exe",
            "snip": "snippingtool.exe",
            "settings": "ms-settings:",
            "windows settings": "ms-settings:",
            "camera": "microsoft.windows.camera:",
            "clock": "ms-clock:",
            "store": "ms-windows-store:",
            "microsoft store": "ms-windows-store:",
            "photos": "ms-photos:",
        }
    )
    
    # Database and Storage paths
    data_dir: Path = USER_DATA_DIR
    db_path: Path = DB_PATH
    logs_dir: Path = LOGS_DIR
    models_dir: Path = MODELS_DIR


config = JarvisConfig()
