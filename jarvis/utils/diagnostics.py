import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict


def get_system_diagnostics() -> Dict[str, Any]:
    """Collects safe system diagnostic information for troubleshooting."""
    diag: Dict[str, Any] = {
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "architecture": platform.architecture()[0],
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "appdata_dir": str(Path.home() / "AppData" / "Local" / "PersonalJarvis"),
    }

    # Audio input capabilities check
    try:
        import sounddevice as sd  # type: ignore
        devices = sd.query_devices()
        diag["audio_devices_count"] = len(devices)
        default_in = sd.default.device[0]
        diag["default_input_device"] = devices[default_in]["name"] if default_in >= 0 else "None"
    except Exception as exc:
        diag["audio_diagnostics_note"] = f"Audio query unavailable: {exc}"

    # Package availability
    packages = ["PySide6", "openai", "faster_whisper", "sounddevice", "openwakeword", "langdetect"]
    availability = {}
    for pkg in packages:
        try:
            mod = __import__(pkg)
            availability[pkg] = getattr(mod, "__version__", "Installed")
        except ImportError:
            availability[pkg] = "Not installed"
    diag["packages"] = availability

    return diag
