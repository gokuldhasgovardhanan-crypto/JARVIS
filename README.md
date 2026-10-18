# Personal JARVIS — Multilingual Windows 11 Personal AI Assistant

A fully functional, modular personal AI desktop assistant engineered with a futuristic **PySide6 holographic HUD** interface, **Faster-Whisper speech recognition**, **Windows SAPI5 / Cloud TTS**, **continuous wake-word engine ("Hey Jarvis")**, **multi-tier multilingual processing across 10 languages**, **hybrid local + cloud AI brain**, and **sandboxed Windows 11 automation**.

---

## System Architecture

```
personal-jarvis/
├── main.py                         # High-DPI Windows 11 application entry point
├── pyproject.toml                  # Build metadata, packaging, and pytest configuration
├── requirements.txt                # Pinned production dependencies
├── .env.example                    # Template environment variables
├── jarvis/
│   ├── config.py                   # Central typed dataclass configuration & paths
│   ├── core/                       # Assistant brain, dispatch & session memory
│   │   ├── assistant.py            # Master orchestrator, language resolution, confirmation gate
│   │   ├── command_registry.py     # Command registration, metadata & help summary
│   │   ├── intent_router.py        # 10-language intent router with mixed-language parser
│   │   └── conversation_manager.py # Multi-turn context window & persistent history
│   ├── memory/                     # Local SQLite WAL-mode memory
│   │   ├── database.py             # Schema migrations, connection pooling & transactions
│   │   └── repository.py           # CRUD for notes, settings, conversations & audit logs
│   ├── languages/                  # Multilingual policy & registry
│   │   ├── registry.py             # 10-language registry with Unicode scripts & markers
│   │   └── policies.py             # Response language policy engine (explicit, auto, priors)
│   ├── ai/                         # Hybrid AI Brain
│   │   ├── base.py                 # Abstract AI provider interfaces
│   │   ├── cloud_provider.py       # OpenAI GPT-4o-mini client
│   │   ├── local_provider.py       # Ollama local LLM + offline resilient template fallback
│   │   └── hybrid_manager.py       # Cloud-first with instant automatic local fallback
│   ├── voice/                      # Voice I/O & Wake-Word
│   │   ├── audio_input.py          # 16kHz PCM streaming, sounddevice capture, level metering
│   │   ├── speech_recognition.py   # Faster-Whisper ONNX STT + Cloud Whisper API
│   │   ├── speech_synthesis.py     # Windows SAPI5 (pyttsx3) + Cloud TTS + capability audit
│   │   ├── wake_word.py            # Continuous "Hey Jarvis" engine with echo suppression
│   │   └── language_detection.py   # Script analysis, Romanized marker parsing, langdetect
│   ├── automation/                 # Windows 11 Sandboxed Automation
│   │   ├── permissions.py          # Application, website & folder allowlist security gate
│   │   └── windows_actions.py      # App launch, folder explorer, file search, volume/media keys, telemetry
│   ├── ui/                         # Futuristic Cyber Dark HUD UI
│   │   ├── hud_widget.py           # 40 FPS dynamic Arc Reactor holographic widget
│   │   ├── memory_panel.py         # Local notes archive & audit trail explorer
│   │   ├── settings_dialog.py      # Neural configuration dialog for AI, voice & languages
│   │   └── main_window.py          # Master HUD desktop window with PTT & continuous listening
│   └── utils/                      # Utilities & Telemetry
│       ├── logging_config.py       # Privacy-aware rotating logger (auto-redacts secrets)
│       └── diagnostics.py          # Audio, hardware, OS & package telemetry
└── tests/                          # 60 automated unit & integration tests
    ├── test_audio_input.py         # Sounddevice enumeration & PCM streaming
    ├── test_configuration.py       # Configuration loading & environment overrides
    ├── test_intent_router.py       # Core intent matching & confirmation prompt tests
    ├── test_language_detection.py  # Script detection, Tanglish/Hinglish, and langdetect
    ├── test_language_registry.py   # 10-language specs & resolution tests
    ├── test_memory.py              # SQLite notes, settings, conversation & audit tests
    ├── test_multilingual_matrix.py # 10-language intent & policy validation matrix
    ├── test_provider_fallback.py   # Hybrid AI cloud-to-local fallback tests
    ├── test_settings.py            # SettingsDialog persistence in SQLite
    ├── test_speech_recognition.py  # Faster-Whisper and cloud STT delegation tests
    ├── test_speech_synthesis.py    # Windows SAPI5 voice capabilities & interruption tests
    ├── test_ui_smoke.py            # 40 FPS HUD animation & UI initialization smoke tests
    ├── test_wake_word.py           # Wake-word debounce, lifecycle & echo suppression tests
    └── test_windows_automation.py  # Windows folder, search, volume/media keys & confirmations
```

---

## 10 Target Languages Matrix

Personal JARVIS supports 10 languages across native scripts, romanized code-switching dialects, intent parsing, and speech synthesis:

| Code | Language | Native Script | Romanized Dialect Examples | STT Provider | Local SAPI TTS | Cloud TTS |
|------|----------|---------------|----------------------------|--------------|----------------|-----------|
| `en` | English | English (Latin) | "what time is it", "open notepad" | Faster-Whisper | ✅ SAPI5 (David/Zira) | ✅ OpenAI TTS |
| `ta` | Tamil | தமிழ் | "neram enna", "notepad open pannu" | Faster-Whisper | Fallback / Cloud | ✅ OpenAI TTS |
| `hi` | Hindi | हिन्दी | "samay kya hai", "calculator kholo" | Faster-Whisper | Fallback / Cloud | ✅ OpenAI TTS |
| `te` | Telugu | తెలుగు | "theedi cheppu", "notepad open cheyi" | Faster-Whisper | Fallback / Cloud | ✅ OpenAI TTS |
| `ml` | Malayalam | മലയാളം | "thiyathi parayu", "notepad open cheyyu" | Faster-Whisper | Fallback / Cloud | ✅ OpenAI TTS |
| `kn` | Kannada | ಕನ್ನಡ | "dinaanka heli", "notepad open maadu" | Faster-Whisper | Fallback / Cloud | ✅ OpenAI TTS |
| `de` | German | Deutsch | "wie spät ist es", "öffne notepad" | Faster-Whisper | ✅ SAPI5 (Hedda/Stefan) | ✅ OpenAI TTS |
| `fr` | French | Français | "quelle heure est-il", "ouvre le bloc-notes" | Faster-Whisper | ✅ SAPI5 (Hortense) | ✅ OpenAI TTS |
| `es` | Spanish | Español | "qué hora es", "abre el bloc de notas" | Faster-Whisper | ✅ SAPI5 (Helena/Laura) | ✅ OpenAI TTS |
| `ja` | Japanese | 日本語 | "今何時ですか", "メモ帳を開いて" | Faster-Whisper | ✅ SAPI5 (Haruka/Ayumi) | ✅ OpenAI TTS |

---

## Windows 11 Installation & Setup

### 1. Prerequisites
- **Operating System**: Windows 11 (or Windows 10 build 19041+)
- **Python**: Python 3.12 - 3.14 (64-bit)
- **Audio**: Microphone & Stereo speakers

### 2. Environment Setup (PowerShell)
```powershell
# Navigate to the project directory
cd personal_jarvis

# Create dedicated virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

*(If PowerShell script execution is restricted, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### 3. Install Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configuration (Optional)
```powershell
Copy-Item .env.example .env
```
To enable online cloud conversations, set your API key in `.env`:
```ini
OPENAI_API_KEY=sk-proj-...
JARVIS_AI_MODE=hybrid
JARVIS_WAKE_PHRASE=hey jarvis
```
*(If unconfigured, JARVIS operates offline seamlessly using local intent routing, Windows SAPI5 speech synthesis, and local template responses).*

---

## How to Run & Deploy

### 1. One-Click Windows 11 Deployment (Desktop & Start Menu)
To install shortcuts with the custom Arc Reactor icon directly to your Windows 11 Desktop and Start Menu:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\create_shortcuts.ps1
```
- **Desktop Shortcut**: `Personal JARVIS.lnk` on your Desktop (launches silently with no command prompt window).
- **Start Menu**: Search for `"Personal JARVIS"` directly in the Windows 11 Start Menu.
- **Autostart on Boot (Optional)**: Run `scripts\register_startup.bat` to launch JARVIS automatically when Windows starts.

### 2. Run Directly via PowerShell
```powershell
.\.venv\Scripts\python.exe main.py
```

### 3. Run Silent Launcher (No Black Terminal)
Double-click `Launch_JARVIS_Silent.vbs` or `Launch_JARVIS.bat`.

### 4. Build Standalone Distributable Binary (.exe)
```powershell
.\.venv\Scripts\python.exe scripts\build_exe.py
```

### 5. Run the Full Automated Test Suite (60 Tests)
```powershell
.\.venv\Scripts\pytest.exe -v
```

---

## Operating Instructions & Voice Controls

### 1. Push-to-Talk (PTT)
- Click the cyan **"🎤 START VOICE (PTT)"** button.
- Speak your command or question in any of the 10 supported languages or mixed dialects.
- Click **"🔴 STOP RECORDING"** or pause speaking. JARVIS transcribes your speech with local Faster-Whisper, processes your intent, updates the HUD, and speaks the reply.

### 2. Continuous Hands-Free Listening ("Hey Jarvis")
- Click **"ENABLE “HEY JARVIS”"** on the left panel.
- Say **"Hey Jarvis"** clearly into the microphone.
- JARVIS pulses the Arc Reactor HUD, transitions to `LISTENING` mode, and captures your spoken command.
- **Echo Suppression**: While JARVIS speaks audio responses, the wake-word engine is automatically suppressed to prevent accidental self-triggering from speaker audio.

### 3. Windows 11 Automation Commands
Personal JARVIS includes sandboxed automation for Windows 11:
- **Application Launching**: "open notepad", "open calculator", "open paint", "open task manager", "open terminal", "notepad open pannu", "calculator kholo".
- **Folder Navigation**: "open downloads folder", "open documents", "open desktop", "downloads open pannu".
- **File Search**: "search files report", "find file notes", "file thedu project".
- **Master Volume Control**: "volume up", "volume down", "mute volume", "volume ethu", "volume badhao".
- **Multimedia Controls**: "play music", "pause music", "next song", "previous track".
- **System Telemetry & Vitals**: "system vitals", "battery status", "laptop charge evlo" (reports CPU load, RAM usage, C: disk space, and battery/AC charging state).
- **Lock Screen**: "lock screen", "lock computer", "pc lock pannu".
- **Sensitive Operations**: "shutdown computer" or "restart computer" triggers an explicit safety confirmation dialog ("yes" / "no") before running the action.

### 4. Local Memory & Persistent Archive
- Save notes: `"remember that buy organic eggs"`, `"note that meeting at 4 PM"`, `"idhai note pannu tomorrow deadline"`.
- Search & View notes: Click **"TOGGLE ARCHIVE"** to inspect or delete stored notes, or say `"show my notes"`.
- Purge notes: `"clear all notes"` (requires confirmation).

### 5. Settings & Diagnostics
- Click **"⚙️ SETTINGS"** to configure AI Mode (Hybrid/Local/Cloud), OpenAI API Key, Whisper model size, Microphone device index, Speech synthesis rate slider (100–250 WPM), and Speech volume slider (10–100%).
- Click **"VOICE CAPABILITIES"** to audit installed local SAPI5 voices and cloud voices for all 10 languages.
- Click **"DIAGNOSTICS"** to inspect hardware, OS, audio input devices, and package versions.

---

## Security & Privacy Highlights
- **100% Local Storage**: SQLite WAL database is stored locally in `%LOCALAPPDATA%\PersonalJarvis\jarvis_memory.db`.
- **Privacy-Aware Logging**: Rotating logger in `%LOCALAPPDATA%\PersonalJarvis\logs\` automatically scrubs and redacts API keys, tokens, and passwords using `PrivacyFilter`.
- **Sandboxed Execution**: `PermissionGate` restricts application execution and folder navigation strictly to allowlisted apps and safe user profile paths.
