import shutil
import winreg
from pathlib import Path
from typing import Tuple, Optional
from jarvis.config import config
from jarvis.utils.logging_config import logger


class PermissionGate:
    """Enforces safety rules, dynamic app discovery, and sensitive action confirmations."""

    @staticmethod
    def resolve_app_path(app_name: str) -> Optional[str]:
        """Dynamically scans Windows Registry App Paths (HKCU & HKLM) for installed apps."""
        clean = app_name.lower().strip().removesuffix(".exe")
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths") as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        sub = winreg.EnumKey(key, i)
                        sub_base = sub.lower().removesuffix(".exe")
                        if clean == sub_base or clean in sub_base:
                            with winreg.OpenKey(key, sub) as sk:
                                val, _ = winreg.QueryValueEx(sk, "")
                                if val and Path(val).exists():
                                    return val
            except Exception:
                pass
        return None

    @staticmethod
    def is_app_allowed(app_name: str) -> Tuple[bool, str]:
        """
        Resolves application executable, UWP protocol scheme, or registry path.
        Returns (is_allowed, launch_target).
        """
        normalized = app_name.lower().strip()

        # 1. Check configured aliases in config
        if normalized in config.approved_apps:
            return True, config.approved_apps[normalized]

        for name, binary in config.approved_apps.items():
            if normalized == binary.lower():
                return True, binary

        # 2. Check Windows UWP URI schemes (e.g., whatsapp:, spotify:, ms-settings:)
        if normalized.endswith(":") or normalized in ["whatsapp", "spotify", "settings", "store", "camera", "clock"]:
            scheme = f"{normalized}:" if not normalized.endswith(":") else normalized
            return True, scheme

        # 3. Dynamic Windows App Paths registry discovery
        reg_path = PermissionGate.resolve_app_path(normalized)
        if reg_path:
            logger.info(f"Dynamically resolved '{app_name}' to registry path: {reg_path}")
            return True, reg_path

        # 4. Check system PATH via shutil.which
        for ext in ["", ".exe", ".cmd", ".bat"]:
            candidate = shutil.which(f"{normalized}{ext}")
            if candidate:
                return True, candidate

        return False, ""

    @staticmethod
    def is_url_allowed(url: str) -> bool:
        """Validates that URL begins with approved HTTP/HTTPS protocol."""
        normalized = url.strip().lower()
        return normalized.startswith("https://") or normalized.startswith("http://")

    @staticmethod
    def requires_confirmation(action_type: str) -> bool:
        """Determines if the action has irreversible or sensitive side-effects."""
        sensitive_actions = {
            "clear_all_notes",
            "clear_history",
            "delete_file",
            "modify_system_setting",
            "shutdown",
            "restart",
        }
        return action_type in sensitive_actions

    @staticmethod
    def is_folder_allowed(path_str: str) -> bool:
        """Ensures target path exists and is a valid accessible directory."""
        try:
            target = Path(path_str).resolve()
            return target.exists() and target.is_dir()
        except Exception:
            return False
