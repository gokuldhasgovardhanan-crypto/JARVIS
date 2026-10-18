from typing import Tuple
from jarvis.config import config
from jarvis.utils.logging_config import logger


class PermissionGate:
    """Enforces safety rules, allowlists, and sensitive action confirmations."""

    @staticmethod
    def is_app_allowed(app_name: str) -> Tuple[bool, str]:
        """Checks if application is in the approved application allowlist."""
        normalized = app_name.lower().strip()
        if normalized in config.approved_apps:
            return True, config.approved_apps[normalized]
        # Check by filename/binary
        for name, binary in config.approved_apps.items():
            if normalized == binary.lower():
                return True, binary
        return False, ""

    @staticmethod
    def is_url_allowed(url: str) -> bool:
        """Validates that URL begins with approved protocol and matches allowlist domain or pattern."""
        normalized = url.strip().lower()
        if not (normalized.startswith("https://") or normalized.startswith("http://")):
            return False
        # Allow pre-approved standard domains
        for approved in config.approved_websites:
            if approved in normalized:
                return True
        return False

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
        """Ensures folder paths stay within the user profile tree."""
        from pathlib import Path
        try:
            target = Path(path_str).resolve()
            home = Path.home().resolve()
            return target == home or home in target.parents
        except Exception:
            return False
