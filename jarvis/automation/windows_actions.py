import os
import re
import time
import threading
import urllib.parse
import subprocess
import webbrowser
import shutil
import ctypes
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from jarvis.automation.permissions import PermissionGate
from jarvis.memory.repository import MemoryRepository
from jarvis.utils.logging_config import logger


# Virtual key codes for Windows multimedia keys
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002


class _SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", wintypes.BYTE),
        ("BatteryFlag", wintypes.BYTE),
        ("BatteryLifePercent", wintypes.BYTE),
        ("SystemStatusFlag", wintypes.BYTE),
        ("BatteryLifeTime", wintypes.DWORD),
        ("BatteryFullLifeTime", wintypes.DWORD),
    ]


class WindowsActionRunner:
    """Safely executes allowlisted Windows 11 tasks with audit logging."""

    def __init__(self, memory_repo: MemoryRepository):
        self.memory_repo = memory_repo

    def launch_app(self, app_name: str) -> Dict[str, Any]:
        """Launches an approved application executable, UWP app, or protocol."""
        allowed, target = PermissionGate.is_app_allowed(app_name)
        if not allowed:
            msg = f"Application '{app_name}' could not be located on this system."
            self.memory_repo.log_action("launch_app", app_name, "rejected", msg)
            return {"success": False, "message": msg}

        try:
            if target.endswith(":") or target.startswith("shell:") or target.startswith("http"):
                os.startfile(target)
            else:
                try:
                    subprocess.Popen([target], shell=False)
                except Exception:
                    os.startfile(target)

            msg = f"Opening {app_name}."
            self.memory_repo.log_action("launch_app", target, "success", msg)
            return {"success": True, "message": msg}
        except Exception as exc:
            err = f"Failed to open {app_name}: {exc}"
            self.memory_repo.log_action("launch_app", target, "failed", err)
            logger.error(err, exc_info=True)
            return {"success": False, "message": err}

    def send_whatsapp_message(self, contact: str, message: str, auto_send: bool = True) -> Dict[str, Any]:
        """
        Launches WhatsApp and composes or sends a message to a contact or phone number.
        Supports international phone numbers (+91...) or contact names.
        """
        clean_contact = contact.strip()
        clean_msg = message.strip()
        if not clean_msg:
            return {"success": False, "message": "WhatsApp message content cannot be empty."}

        encoded_text = urllib.parse.quote(clean_msg)
        
        # Check if contact is a phone number (7+ digits)
        digits_only = re.sub(r"[^\d+]", "", clean_contact)
        has_digits = len(re.sub(r"[^\d]", "", clean_contact)) >= 7

        if has_digits:
            phone_num = re.sub(r"[^\d]", "", digits_only)
            target_uri = f"whatsapp://send?phone={phone_num}&text={encoded_text}"
            web_fallback = f"https://web.whatsapp.com/send?phone={phone_num}&text={encoded_text}"
            contact_label = f"number +{phone_num}"
        else:
            target_uri = f"whatsapp://send?text={encoded_text}"
            web_fallback = f"https://web.whatsapp.com/send?text={encoded_text}"
            contact_label = f"'{clean_contact}'"

        try:
            # Launch WhatsApp Desktop via URI protocol
            os.startfile(target_uri)
            msg = f"Opening WhatsApp and sending message to {contact_label}: \"{clean_msg}\"."
            
            # If auto_send is requested, simulate Enter key dispatch after window focuses
            if auto_send:
                def _dispatch_enter():
                    time.sleep(2.5)
                    try:
                        # VK_RETURN = 0x0D
                        ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)
                        ctypes.windll.user32.keybd_event(0x0D, 0, KEYEVENTF_KEYUP, 0)
                        logger.info("Sent Enter key event to WhatsApp.")
                    except Exception as exc:
                        logger.debug(f"Enter key dispatch notice: {exc}")

                threading.Thread(target=_dispatch_enter, daemon=True).start()

            self.memory_repo.log_action("whatsapp_message", clean_contact, "success", msg)
            return {"success": True, "message": msg, "contact": clean_contact, "text": clean_msg}
        except Exception as exc:
            # Fallback to WhatsApp Web in browser
            try:
                webbrowser.open(web_fallback)
                fallback_msg = f"Opened WhatsApp Web to message {contact_label}: \"{clean_msg}\"."
                self.memory_repo.log_action("whatsapp_message", clean_contact, "success", fallback_msg)
                return {"success": True, "message": fallback_msg}
            except Exception as web_exc:
                err = f"Failed to send WhatsApp message: {exc}; Web fallback error: {web_exc}"
                self.memory_repo.log_action("whatsapp_message", clean_contact, "failed", err)
                logger.error(err, exc_info=True)
                return {"success": False, "message": err}

    def take_screenshot(self) -> Dict[str, Any]:
        """Triggers Windows screenshot capture tool."""
        try:
            try:
                os.startfile("ms-screenclip:")
            except Exception:
                subprocess.Popen(["snippingtool.exe"])
            msg = "Screen capture tool activated. Select the area to save."
            self.memory_repo.log_action("take_screenshot", "screen", "success", msg)
            return {"success": True, "message": msg}
        except Exception as exc:
            err = f"Failed to activate screenshot tool: {exc}"
            self.memory_repo.log_action("take_screenshot", "screen", "failed", err)
            return {"success": False, "message": err}

    def open_website(self, url: str) -> Dict[str, Any]:
        """Opens an approved website in the default browser."""
        # Auto-prefix https if missing
        full_url = url if url.startswith("http") else f"https://{url}"
        if not PermissionGate.is_url_allowed(full_url):
            msg = f"Access to '{full_url}' is not in the approved websites list."
            self.memory_repo.log_action("open_website", full_url, "rejected", msg)
            return {"success": False, "message": msg}

        try:
            webbrowser.open(full_url)
            msg = f"Navigating to {full_url}."
            self.memory_repo.log_action("open_website", full_url, "success", msg)
            return {"success": True, "message": msg}
        except Exception as exc:
            err = f"Failed to open website: {exc}"
            self.memory_repo.log_action("open_website", full_url, "failed", err)
            logger.error(err, exc_info=True)
            return {"success": False, "message": err}

    def open_folder(self, folder_alias: str) -> Dict[str, Any]:
        """Opens a known user folder or safe directory in Windows File Explorer."""
        folder_alias_lower = folder_alias.lower().strip()
        home = Path.home()
        known_folders = {
            "downloads": home / "Downloads",
            "download": home / "Downloads",
            "documents": home / "Documents",
            "document": home / "Documents",
            "desktop": home / "Desktop",
            "pictures": home / "Pictures",
            "picture": home / "Pictures",
            "photos": home / "Pictures",
            "music": home / "Music",
            "videos": home / "Videos",
            "home": home,
            "user": home,
        }

        target_path: Optional[Path] = None
        for alias, path in known_folders.items():
            if alias in folder_alias_lower:
                target_path = path
                break

        if not target_path:
            candidate = Path(folder_alias).expanduser()
            if candidate.exists() and PermissionGate.is_folder_allowed(str(candidate)):
                target_path = candidate

        if not target_path or not target_path.exists():
            msg = f"Folder '{folder_alias}' not found or access is restricted."
            self.memory_repo.log_action("open_folder", folder_alias, "rejected", msg)
            return {"success": False, "message": msg}

        try:
            subprocess.Popen(["explorer.exe", str(target_path)])
            msg = f"Opening {target_path.name or 'Home'} folder."
            self.memory_repo.log_action("open_folder", str(target_path), "success", msg)
            return {"success": True, "message": msg, "path": str(target_path)}
        except Exception as exc:
            err = f"Failed to open folder: {exc}"
            self.memory_repo.log_action("open_folder", str(target_path), "failed", err)
            logger.error(err, exc_info=True)
            return {"success": False, "message": err}

    def search_files(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Safely searches user folders for files matching query."""
        clean_q = query.strip().lower()
        if not clean_q or len(clean_q) < 2:
            return {"success": False, "message": "Search query too short. Provide at least 2 characters."}

        search_roots = [
            Path.home() / "Documents",
            Path.home() / "Downloads",
            Path.home() / "Desktop",
        ]
        ignored_names = {".git", "appdata", "node_modules", "__pycache__", ".venv", "temp"}

        matches: List[Dict[str, str]] = []
        for root in search_roots:
            if not root.exists():
                continue
            for root_dir, dir_names, file_names in os.walk(root):
                dir_names[:] = [d for d in dir_names if d.lower() not in ignored_names and not d.startswith(".")]
                try:
                    depth = len(Path(root_dir).relative_to(root).parts)
                    if depth > 3:
                        continue
                except Exception:
                    continue

                for f in file_names:
                    if clean_q in f.lower():
                        full_p = Path(root_dir) / f
                        matches.append({"name": f, "path": str(full_p)})
                        if len(matches) >= max_results:
                            break
                if len(matches) >= max_results:
                    break
            if len(matches) >= max_results:
                break

        msg = f"Found {len(matches)} matching file(s) for '{query}'."
        self.memory_repo.log_action("search_files", query, "success", msg)
        return {"success": True, "message": msg, "matches": matches}

    def control_volume(self, action: str, steps: int = 2) -> Dict[str, Any]:
        """Adjusts master system audio volume via Windows virtual key events."""
        action_lower = action.lower().strip()
        vk = None
        desc = ""
        loop_count = 1

        if any(w in action_lower for w in ["up", "increase", "raise", "louder"]):
            vk = VK_VOLUME_UP
            loop_count = max(1, min(steps, 10))
            desc = f"Increased system volume by {loop_count * 2}%."
        elif any(w in action_lower for w in ["down", "decrease", "lower", "quieter"]):
            vk = VK_VOLUME_DOWN
            loop_count = max(1, min(steps, 10))
            desc = f"Decreased system volume by {loop_count * 2}%."
        elif any(w in action_lower for w in ["mute", "unmute"]):
            vk = VK_VOLUME_MUTE
            desc = "Toggled master volume mute."
        else:
            return {"success": False, "message": f"Unsupported volume command: {action}"}

        try:
            for _ in range(loop_count):
                ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
                ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
            self.memory_repo.log_action("control_volume", action, "success", desc)
            return {"success": True, "message": desc}
        except Exception as exc:
            err = f"Failed to adjust volume: {exc}"
            self.memory_repo.log_action("control_volume", action, "failed", err)
            logger.error(err, exc_info=True)
            return {"success": False, "message": err}

    def control_media(self, action: str) -> Dict[str, Any]:
        """Controls media playback (play/pause, next, previous, stop)."""
        act_lower = action.lower().strip()
        vk = None
        desc = ""

        if any(w in act_lower for w in ["play", "pause", "toggle"]):
            vk = VK_MEDIA_PLAY_PAUSE
            desc = "Toggled media play/pause."
        elif any(w in act_lower for w in ["next", "skip", "forward"]):
            vk = VK_MEDIA_NEXT_TRACK
            desc = "Skipped to next track."
        elif any(w in act_lower for w in ["prev", "previous", "back"]):
            vk = VK_MEDIA_PREV_TRACK
            desc = "Returned to previous track."
        elif "stop" in act_lower:
            vk = VK_MEDIA_STOP
            desc = "Stopped media playback."
        else:
            return {"success": False, "message": f"Unsupported media command: {action}"}

        try:
            ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
            ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
            self.memory_repo.log_action("control_media", action, "success", desc)
            return {"success": True, "message": desc}
        except Exception as exc:
            err = f"Failed to execute media control: {exc}"
            self.memory_repo.log_action("control_media", action, "failed", err)
            logger.error(err, exc_info=True)
            return {"success": False, "message": err}

    def get_system_vitals(self) -> Dict[str, Any]:
        """Queries CPU, memory, disk, and battery telemetry."""
        vitals: Dict[str, Any] = {}
        try:
            import psutil
            vitals["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            vitals["ram_percent"] = mem.percent
            vitals["ram_used_gb"] = round((mem.total - mem.available) / (1024**3), 1)
            vitals["ram_total_gb"] = round(mem.total / (1024**3), 1)
        except Exception:
            vitals["cpu_percent"] = "N/A"
            vitals["ram_percent"] = "N/A"

        try:
            du = shutil.disk_usage("C:")
            vitals["disk_used_percent"] = round((du.used / du.total) * 100, 1)
            vitals["disk_free_gb"] = round(du.free / (1024**3), 1)
            vitals["disk_total_gb"] = round(du.total / (1024**3), 1)
        except Exception:
            vitals["disk_used_percent"] = "N/A"

        try:
            sps = _SYSTEM_POWER_STATUS()
            if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(sps)):
                vitals["battery_percent"] = int(sps.BatteryLifePercent) if sps.BatteryLifePercent <= 100 else "AC Only"
                vitals["is_plugged_in"] = sps.ACLineStatus == 1
            else:
                vitals["battery_percent"] = "Desktop/AC"
                vitals["is_plugged_in"] = True
        except Exception:
            vitals["battery_percent"] = "N/A"
            vitals["is_plugged_in"] = True

        msg = (
            f"JARVIS System Vitals:\n"
            f"• CPU Load: {vitals.get('cpu_percent')}%\n"
            f"• RAM: {vitals.get('ram_percent')}% used ({vitals.get('ram_used_gb', '?')}/{vitals.get('ram_total_gb', '?')} GB)\n"
            f"• Disk (C:): {vitals.get('disk_used_percent')}% used ({vitals.get('disk_free_gb', '?')} GB free)\n"
            f"• Battery: {vitals.get('battery_percent')}% ({'Plugged In' if vitals.get('is_plugged_in') else 'On Battery'})"
        )
        return {"success": True, "message": msg, "vitals": vitals}

    def system_power(self, action: str, confirmed: bool = False) -> Dict[str, Any]:
        """Manages lock screen, shutdown, or restart commands with safety checks."""
        act_lower = action.lower().strip()
        if "lock" in act_lower:
            try:
                ctypes.windll.user32.LockWorkStation()
                self.memory_repo.log_action("system_power", "lock", "success", "Workstation locked.")
                return {"success": True, "message": "Workstation locked."}
            except Exception as exc:
                err = f"Failed to lock workstation: {exc}"
                return {"success": False, "message": err}

        if "shutdown" in act_lower:
            if not confirmed:
                return {
                    "success": False,
                    "requires_confirmation": True,
                    "confirmation_prompt": "Are you sure you want to shut down this computer?",
                    "message": "Shutdown request requires explicit confirmation."
                }
            subprocess.Popen(["shutdown", "/s", "/t", "30"])
            self.memory_repo.log_action("system_power", "shutdown", "success", "Shutdown scheduled in 30s.")
            return {"success": True, "message": "Shutdown sequence initiated. System will power down in 30 seconds."}

        if "restart" in act_lower or "reboot" in act_lower:
            if not confirmed:
                return {
                    "success": False,
                    "requires_confirmation": True,
                    "confirmation_prompt": "Are you sure you want to restart this computer?",
                    "message": "Restart request requires explicit confirmation."
                }
            subprocess.Popen(["shutdown", "/r", "/t", "30"])
            self.memory_repo.log_action("system_power", "restart", "success", "Restart scheduled in 30s.")
            return {"success": True, "message": "Restart sequence initiated. System will reboot in 30 seconds."}

        if "cancel" in act_lower:
            subprocess.Popen(["shutdown", "/a"])
            self.memory_repo.log_action("system_power", "cancel_shutdown", "success", "Shutdown aborted.")
            return {"success": True, "message": "Pending shutdown or restart has been cancelled."}

        return {"success": False, "message": f"Unknown system power command: {action}"}
