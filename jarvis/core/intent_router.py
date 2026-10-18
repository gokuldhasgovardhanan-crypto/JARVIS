from datetime import datetime
import re
from typing import Optional, Dict, Any, List
from jarvis.core.command_registry import CommandRegistry, Command, ActionResult
from jarvis.automation.windows_actions import WindowsActionRunner
from jarvis.memory.repository import MemoryRepository
from jarvis.languages.registry import language_registry
from jarvis.utils.diagnostics import get_system_diagnostics
from jarvis.utils.logging_config import logger
from jarvis.config import config


class IntentRouter:
    """Routes user queries across 10 languages and mixed dialects to registered local commands."""

    def __init__(self, memory_repo: MemoryRepository, action_runner: WindowsActionRunner):
        self.memory = memory_repo
        self.actions = action_runner
        self.registry = CommandRegistry()
        self._register_default_commands()

    def _register_default_commands(self) -> None:
        # 1. Time command
        self.registry.register(
            Command(
                intent="get_time",
                description="Reports the current time.",
                handler=lambda **kw: ActionResult(
                    success=True,
                    message=f"The current time is {datetime.now().strftime('%I:%M %p')}."
                ),
                multilingual_examples={
                    "en": ["what time is it", "tell me the time", "current time", "what's the time"],
                    "ta": ["neram enna", "enna time", "time sollu", "ippo neram enna", "நேரம் என்ன"],
                    "hi": ["kya samay hua hai", "time kya hai", "samay batao", "kitna baje hai", "समय क्या है"],
                    "te": ["samayam entha", "time entha", "time cheppu", "సమయం ఎంత"],
                    "ml": ["samayam enthaanu", "time parayu", "ഇപ്പോൾ സമയം എത്ര"],
                    "kn": ["samaya enu", "time heli", "ಈಗ ಸಮಯ ಎಷ್ಟು"],
                    "de": ["wie spät ist es", "wie viel uhr ist es", "sag mir die uhrzeit"],
                    "fr": ["quelle heure est-il", "donne-moi l'heure", "l'heure actuelle"],
                    "es": ["qué hora es", "dime la hora", "hora actual"],
                    "ja": ["今何時ですか", "時間を教えて", "何時ですか"],
                },
            )
        )

        # 2. Date command
        self.registry.register(
            Command(
                intent="get_date",
                description="Reports today's date.",
                handler=lambda **kw: ActionResult(
                    success=True,
                    message=f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."
                ),
                multilingual_examples={
                    "en": ["what is today's date", "what's the date", "today date", "tell me the date"],
                    "ta": ["innaiku enna thethi", "today date enna", "thethi sollu", "இன்று என்ன தேதி"],
                    "hi": ["aaj kaun si tarikh hai", "aaj ki tarikh kya hai", "aaj ka din kya hai", "आज क्या तारीख है"],
                    "te": ["theedi cheppu", "ee roju theedi entha", "ఈ రోజు తేదీ ఎంత"],
                    "ml": ["thiyathi parayu", "innu enthaanu thiyathi", "ഇന്ന് എന്ത് തീയതി"],
                    "kn": ["dinaanka heli", "ivatthu dinaanka enu", "ಇಂದು ದಿನಾಂಕ ಎಷ್ಟು"],
                    "de": ["welches datum haben wir heute", "welcher tag ist heute", "sag mir das datum"],
                    "fr": ["quelle est la date d'aujourd'hui", "quel jour sommes-nous"],
                    "es": ["cuál es la fecha de hoy", "qué día es hoy"],
                    "ja": ["今日の日付は何ですか", "今日は何日ですか", "何日ですか"],
                },
            )
        )

        # 3. Open Notepad
        self.registry.register(
            Command(
                intent="open_notepad",
                description="Launches Windows Notepad.",
                handler=lambda **kw: ActionResult(**self.actions.launch_app("notepad")),
                multilingual_examples={
                    "en": ["open notepad", "launch notepad", "start notepad"],
                    "ta": ["notepad open pannu", "notepad theravum", "நோட்பேட் திற"],
                    "hi": ["notepad kholo", "notepad open karo", "नोटपैड खोलो"],
                    "te": ["notepad open cheyi", "notepad theruvu"],
                    "ml": ["notepad open cheyyu", "notepad thurakku"],
                    "kn": ["notepad open maadu", "notepad there"],
                    "de": ["öffne notepad", "notepad starten"],
                    "fr": ["ouvre le bloc-notes", "lance notepad"],
                    "es": ["abre el bloc de notas", "iniciar notepad"],
                    "ja": ["メモ帳を開いて", "ノートパッドを開いて"],
                },
            )
        )

        # 4. Open Calculator
        self.registry.register(
            Command(
                intent="open_calculator",
                description="Launches Windows Calculator.",
                handler=lambda **kw: ActionResult(**self.actions.launch_app("calculator")),
                multilingual_examples={
                    "en": ["open calculator", "launch calc", "open calc", "start calculator"],
                    "ta": ["calculator open pannu", "calc open pannu"],
                    "hi": ["calculator kholo", "calc start karo", "कैलकुलेटर खोलो"],
                    "te": ["calculator open cheyi", "calc open cheyi"],
                    "ml": ["calculator open cheyyu", "calc thurakku"],
                    "kn": ["calculator open maadu", "calc open maadu"],
                    "de": ["öffne rechner", "taschenrechner starten"],
                    "fr": ["ouvre la calculatrice", "lance la calculatrice"],
                    "es": ["abre la calculadora", "iniciar calculadora"],
                    "ja": ["電卓を開いて", "計算機を開いて"],
                },
            )
        )

        # 5. Open Paint
        self.registry.register(
            Command(
                intent="open_paint",
                description="Launches Microsoft Paint.",
                handler=lambda **kw: ActionResult(**self.actions.launch_app("paint")),
                multilingual_examples={
                    "en": ["open paint", "launch paint", "open mspaint"],
                    "ta": ["paint open pannu", "paint theravum"],
                    "hi": ["paint kholo", "paint open karo"],
                    "de": ["öffne paint"],
                    "fr": ["ouvre paint"],
                    "es": ["abre paint"],
                },
            )
        )

        # 6. Open Task Manager
        self.registry.register(
            Command(
                intent="open_task_manager",
                description="Launches Windows Task Manager.",
                handler=lambda **kw: ActionResult(**self.actions.launch_app("task manager")),
                multilingual_examples={
                    "en": ["open task manager", "launch task manager", "open taskmgr"],
                    "ta": ["task manager open pannu", "task manager theravum"],
                    "hi": ["task manager kholo"],
                    "de": ["öffne taskmanager", "task manager starten"],
                },
            )
        )

        # 7. Open Terminal
        self.registry.register(
            Command(
                intent="open_terminal",
                description="Launches Windows Command Prompt or Terminal.",
                handler=lambda **kw: ActionResult(**self.actions.launch_app("cmd")),
                multilingual_examples={
                    "en": ["open terminal", "launch terminal", "open cmd", "open command prompt"],
                    "ta": ["terminal open pannu", "cmd open pannu"],
                    "hi": ["terminal kholo", "cmd kholo"],
                    "de": ["öffne terminal", "eingabeaufforderung starten"],
                },
            )
        )

        # 8. Open YouTube
        self.registry.register(
            Command(
                intent="open_youtube",
                description="Opens YouTube in the default browser.",
                handler=lambda **kw: ActionResult(**self.actions.open_website("https://www.youtube.com")),
                multilingual_examples={
                    "en": ["open youtube", "launch youtube"],
                    "ta": ["youtube open pannu", "youtube theravum"],
                    "hi": ["youtube kholo", "youtube open karo"],
                    "de": ["öffne youtube"],
                },
            )
        )

        # 9. Open Google
        self.registry.register(
            Command(
                intent="open_google",
                description="Opens Google search in the default browser.",
                handler=lambda **kw: ActionResult(**self.actions.open_website("https://www.google.com")),
                multilingual_examples={
                    "en": ["open google", "launch google search"],
                    "ta": ["google open pannu"],
                    "hi": ["google kholo"],
                    "de": ["öffne google"],
                },
            )
        )

        # 10. Open Folder
        self.registry.register(
            Command(
                intent="open_folder",
                description="Opens user folders in Windows File Explorer.",
                handler=self._handle_open_folder,
                multilingual_examples={
                    "en": ["open downloads", "open documents", "open desktop", "open folder", "open pictures"],
                    "ta": ["downloads open pannu", "documents open pannu", "desktop open pannu"],
                    "hi": ["downloads kholo", "documents kholo", "desktop kholo"],
                    "te": ["downloads open cheyi", "documents open cheyi"],
                    "ml": ["downloads open cheyyu", "documents thurakku"],
                    "kn": ["downloads open maadu", "documents there"],
                    "de": ["öffne downloads", "öffne dokumente", "öffne desktop"],
                    "fr": ["ouvre les téléchargements", "ouvre les documents"],
                    "es": ["abre descargas", "abre documentos"],
                    "ja": ["ダウンロードを開いて", "ドキュメントを開いて"],
                },
            )
        )

        # 11. Search Files
        self.registry.register(
            Command(
                intent="search_files",
                description="Searches for files across user folders.",
                handler=self._handle_search_files,
                multilingual_examples={
                    "en": ["search file <query>", "find file <query>", "search for file <query>"],
                    "ta": ["file thedu <query>", "file search pannu <query>"],
                    "hi": ["file dhoondho <query>", "file search karo <query>"],
                    "de": ["datei suchen <query>", "finde datei <query>"],
                    "fr": ["cherche le fichier <query>"],
                    "es": ["buscar archivo <query>"],
                },
            )
        )

        # 12. Volume Up
        self.registry.register(
            Command(
                intent="volume_up",
                description="Increases system master volume.",
                handler=lambda **kw: ActionResult(**self.actions.control_volume("up")),
                multilingual_examples={
                    "en": ["volume up", "increase volume", "raise volume", "louder"],
                    "ta": ["volume ethu", "volume athigam pannu", "satham ethu"],
                    "hi": ["volume badhao", "awaz badhao", "volume tez karo"],
                    "te": ["volume penchu", "sound penchu"],
                    "ml": ["volume koottu"],
                    "kn": ["volume hecchisu"],
                    "de": ["lautstärke erhöhen", "lauter machen", "lauter"],
                    "fr": ["monte le son", "augmente le volume"],
                    "es": ["sube el volumen", "aumenta el volumen"],
                    "ja": ["音量を上げて", "ボリュームを上げて"],
                },
            )
        )

        # 13. Volume Down
        self.registry.register(
            Command(
                intent="volume_down",
                description="Decreases system master volume.",
                handler=lambda **kw: ActionResult(**self.actions.control_volume("down")),
                multilingual_examples={
                    "en": ["volume down", "decrease volume", "lower volume", "quieter"],
                    "ta": ["volume kora", "volume kammi pannu", "satham kora"],
                    "hi": ["volume kam karo", "awaz dheemi karo"],
                    "te": ["volume thagginchu"],
                    "ml": ["volume kurakku"],
                    "kn": ["volume kadime maadu"],
                    "de": ["lautstärke verringern", "leiser machen", "leiser"],
                    "fr": ["baisse le son", "diminue le volume"],
                    "es": ["baja el volumen", "reduce el volumen"],
                    "ja": ["音量を下げて", "ボリュームを下げて"],
                },
            )
        )

        # 14. Volume Mute
        self.registry.register(
            Command(
                intent="volume_mute",
                description="Toggles master volume mute.",
                handler=lambda **kw: ActionResult(**self.actions.control_volume("mute")),
                multilingual_examples={
                    "en": ["mute volume", "mute audio", "unmute volume", "mute sound", "mute"],
                    "ta": ["volume mute pannu", "satham niruthu", "mute pannu"],
                    "hi": ["volume mute karo", "awaz band karo", "mute karo"],
                    "te": ["volume mute cheyi"],
                    "ml": ["mute cheyyu"],
                    "kn": ["mute maadu"],
                    "de": ["ton stummschalten", "stummschalten", "ton an"],
                    "fr": ["coupe le son", "silence"],
                    "es": ["silenciar volumen", "silenciar audio"],
                    "ja": ["ミュートにして", "消音にして"],
                },
            )
        )

        # 15. Media Play / Pause
        self.registry.register(
            Command(
                intent="media_play_pause",
                description="Toggles multimedia playback (play/pause).",
                handler=lambda **kw: ActionResult(**self.actions.control_media("play_pause")),
                multilingual_examples={
                    "en": ["play music", "pause music", "toggle playback", "play pause"],
                    "ta": ["paata podu", "paata niruthu", "music play pannu", "music pause pannu"],
                    "hi": ["gaana chalao", "gaana roko", "music play karo", "music pause karo"],
                    "te": ["paata paadu", "paata aapu"],
                    "de": ["musik abspielen", "musik pausieren"],
                    "fr": ["jouer la musique", "mettre en pause la musique"],
                    "es": ["reproducir música", "pausar música"],
                },
            )
        )

        # 16. Media Next Track
        self.registry.register(
            Command(
                intent="media_next",
                description="Skips to next media track.",
                handler=lambda **kw: ActionResult(**self.actions.control_media("next")),
                multilingual_examples={
                    "en": ["next song", "next track", "skip song", "next music"],
                    "ta": ["adutha paatu", "next song podu"],
                    "hi": ["agla gaana", "next song chalao"],
                    "de": ["nächstes lied", "nächster titel"],
                },
            )
        )

        # 17. Media Prev Track
        self.registry.register(
            Command(
                intent="media_prev",
                description="Returns to previous media track.",
                handler=lambda **kw: ActionResult(**self.actions.control_media("prev")),
                multilingual_examples={
                    "en": ["previous song", "previous track", "last song"],
                    "ta": ["munthaiya paatu", "previous song podu"],
                    "hi": ["pichla gaana"],
                    "de": ["vorheriges lied"],
                },
            )
        )

        # 18. System Vitals / Performance
        self.registry.register(
            Command(
                intent="system_vitals",
                description="Reports CPU, RAM, Disk, and Battery telemetry.",
                handler=self._handle_system_vitals,
                multilingual_examples={
                    "en": ["system vitals", "system health", "cpu usage", "battery status", "pc performance", "hardware status"],
                    "ta": ["system vitals enna", "battery status enna", "laptop charge evlo", "system epdi irukku"],
                    "hi": ["system vitals kya hai", "battery kitni hai", "system ki sthiti"],
                    "te": ["battery entha undi", "system health entha"],
                    "de": ["systemstatus", "akkustand", "systemleistung"],
                    "fr": ["état du système", "niveau de batterie"],
                    "es": ["estado del sistema", "nivel de batería"],
                    "ja": ["システムの状態", "バッテリー残量"],
                },
            )
        )

        # 19. Lock Workstation
        self.registry.register(
            Command(
                intent="lock_workstation",
                description="Locks the Windows workstation screen.",
                handler=lambda **kw: ActionResult(**self.actions.system_power("lock")),
                multilingual_examples={
                    "en": ["lock screen", "lock computer", "lock pc", "lock workstation"],
                    "ta": ["screen lock pannu", "pc lock pannu", "computer lock pannu"],
                    "hi": ["screen lock karo", "pc lock karo", "computer lock karo"],
                    "te": ["screen lock cheyi", "pc lock cheyi"],
                    "ml": ["screen lock cheyyu"],
                    "kn": ["screen lock maadu"],
                    "de": ["bildschirm sperren", "computer sperren"],
                    "fr": ["verrouiller l'écran", "verrouiller l'ordinateur"],
                    "es": ["bloquear pantalla", "bloquear equipo"],
                    "ja": ["画面をロックして", "PCをロックして"],
                },
            )
        )

        # 20. Shutdown Computer (Sensitive, requires confirmation)
        self.registry.register(
            Command(
                intent="shutdown_system",
                description="Powers down the computer (requires confirmation).",
                handler=self._handle_shutdown,
                is_sensitive=True,
                multilingual_examples={
                    "en": ["shutdown computer", "turn off pc", "shutdown system", "power off"],
                    "ta": ["computer shutdown pannu", "pc off pannu"],
                    "hi": ["computer band karo", "pc shutdown karo"],
                    "de": ["computer herunterfahren", "system ausschalten"],
                    "fr": ["éteindre l'ordinateur", "arrêter le système"],
                    "es": ["apagar el equipo", "apagar la computadora"],
                    "ja": ["コンピューターをシャットダウンして", "PCの電源を切って"],
                },
            )
        )

        # 21. Restart Computer (Sensitive, requires confirmation)
        self.registry.register(
            Command(
                intent="restart_system",
                description="Reboots the computer (requires confirmation).",
                handler=self._handle_restart,
                is_sensitive=True,
                multilingual_examples={
                    "en": ["restart computer", "reboot pc", "reboot system", "restart pc"],
                    "ta": ["computer restart pannu", "pc restart pannu"],
                    "hi": ["computer restart karo", "pc restart karo"],
                    "de": ["computer neu starten", "system neu starten"],
                    "fr": ["redémarrer l'ordinateur"],
                    "es": ["reiniciar el equipo", "reiniciar la computadora"],
                    "ja": ["コンピューターを再起動して", "PCを再起動して"],
                },
            )
        )

        # 22. Save note
        self.registry.register(
            Command(
                intent="save_note",
                description="Saves a note to local persistent memory.",
                handler=self._handle_save_note,
                multilingual_examples={
                    "en": ["remember that <text>", "note that <text>", "save note <text>"],
                    "ta": ["idhai note pannu <text>", "remember pannu <text>"],
                    "hi": ["yaad rakho ki <text>", "note karo <text>"],
                    "te": ["idi gurtupettuko <text>"],
                    "ml": ["ithu ormakkuka <text>"],
                    "kn": ["idannu nenapidi <text>"],
                    "de": ["merk dir dass <text>", "speichere notiz <text>"],
                },
            )
        )

        # 23. Read notes
        self.registry.register(
            Command(
                intent="get_notes",
                description="Reads back your saved local notes.",
                handler=self._handle_get_notes,
                multilingual_examples={
                    "en": ["show my notes", "read my notes", "what do you remember", "list notes"],
                    "ta": ["ennudaiya notes kaattu", "notes enna", "show notes"],
                    "hi": ["meri notes dikhao", "kya yaad hai"],
                    "de": ["zeige meine notizen", "lies meine notizen"],
                },
            )
        )

        # 24. Clear notes (Requires confirmation)
        self.registry.register(
            Command(
                intent="clear_notes",
                description="Deletes all stored local notes.",
                handler=self._handle_clear_notes,
                is_sensitive=True,
                multilingual_examples={
                    "en": ["clear all notes", "delete all notes"],
                    "ta": ["notes ellam azhithuvidu", "clear notes"],
                    "hi": ["saari notes mita do", "clear notes"],
                    "de": ["lösche alle notizen"],
                },
            )
        )

        # 25. System Diagnostics
        self.registry.register(
            Command(
                intent="diagnostics",
                description="Reports local system status and diagnostics.",
                handler=self._handle_diagnostics,
                multilingual_examples={
                    "en": ["system status", "diagnostics", "check system", "jarvis status"],
                },
            )
        )

        # 26. Set Preferred Response Language
        self.registry.register(
            Command(
                intent="set_language",
                description="Changes your preferred JARVIS response language.",
                handler=self._handle_set_language,
                multilingual_examples={
                    "en": ["set language to <lang>", "change response language to <lang>", "switch to <lang>"],
                    "ta": ["tamil-la pesu", "mozhia maathu"],
                    "hi": ["hindi mein bolo", "bhasha badlo"],
                    "de": ["sprich deutsch", "sprache ändern"],
                },
            )
        )

        # 27. Translate Text
        self.registry.register(
            Command(
                intent="translate_text",
                description="Translates text between supported languages.",
                handler=self._handle_translate,
                multilingual_examples={
                    "en": ["translate <text> to <lang>", "translate <text> into <lang>"],
                    "ta": ["translate pannu <text>"],
                    "hi": ["translate karo <text>"],
                    "de": ["übersetze <text> ins <lang>"],
                },
            )
        )

        # 28. Help
        self.registry.register(
            Command(
                intent="help",
                description="Lists available commands and usage guidance.",
                handler=lambda **kw: ActionResult(
                    success=True,
                    message=self.registry.get_help_summary()
                ),
                multilingual_examples={
                    "en": ["help", "what can you do", "commands"],
                    "ta": ["udhavi", "enna panna mudiyum"],
                    "hi": ["madad", "aap kya kar sakte ho"],
                    "de": ["hilfe", "was kannst du tun"],
                },
            )
        )

    # --- Handlers ---
    def _handle_open_folder(self, folder: str = "downloads", **kw) -> ActionResult:
        res = self.actions.open_folder(folder)
        return ActionResult(
            success=res.get("success", False),
            message=res.get("message", ""),
            intent="open_folder",
            data=res,
        )

    def _handle_system_vitals(self, **kw) -> ActionResult:
        res = self.actions.get_system_vitals()
        return ActionResult(
            success=res.get("success", True),
            message=res.get("message", ""),
            intent="system_vitals",
            data=res.get("vitals"),
        )

    def _handle_search_files(self, query: str = "", **kw) -> ActionResult:
        clean_q = query.strip()
        if not clean_q:
            return ActionResult(success=False, message="Please specify what file to search for.", intent="search_files")
        res = self.actions.search_files(clean_q)
        matches = res.get("matches", [])
        if not matches:
            return ActionResult(success=True, message=f"No files found matching '{clean_q}'.", intent="search_files")
        formatted = "\n".join([f"• {m['name']} ({m['path']})" for m in matches[:6]])
        return ActionResult(
            success=True,
            message=f"Found {len(matches)} file(s) matching '{clean_q}':\n{formatted}",
            intent="search_files",
            data=res,
        )

    def _handle_shutdown(self, confirmed: bool = False, **kw) -> ActionResult:
        res = self.actions.system_power("shutdown", confirmed=confirmed)
        return ActionResult(
            success=res.get("success", False),
            message=res.get("message", ""),
            requires_confirmation=res.get("requires_confirmation", False),
            confirmation_prompt=res.get("confirmation_prompt", ""),
            intent="shutdown_system",
        )

    def _handle_restart(self, confirmed: bool = False, **kw) -> ActionResult:
        res = self.actions.system_power("restart", confirmed=confirmed)
        return ActionResult(
            success=res.get("success", False),
            message=res.get("message", ""),
            requires_confirmation=res.get("requires_confirmation", False),
            confirmation_prompt=res.get("confirmation_prompt", ""),
            intent="restart_system",
        )

    def _handle_save_note(self, content: str = "", **kw) -> ActionResult:
        if not content:
            return ActionResult(
                success=False,
                message="Please provide the text you would like me to remember."
            )
        note_id = self.memory.save_note(content)
        return ActionResult(
            success=True,
            message=f"I've saved that note in your local memory (Note #{note_id}).",
            data={"note_id": note_id, "note": content}
        )

    def _handle_get_notes(self, **kw) -> ActionResult:
        notes = self.memory.get_notes(limit=10)
        if not notes:
            return ActionResult(success=True, message="Your local notes archive is currently empty.")
        formatted = "\n".join([f"• [{n['id']}] {n['note']}" for n in notes])
        return ActionResult(
            success=True,
            message=f"Here are your most recent saved notes:\n{formatted}",
            data={"notes": notes}
        )

    def _handle_clear_notes(self, confirmed: bool = False, **kw) -> ActionResult:
        if not confirmed:
            return ActionResult(
                success=False,
                message="Clearing all notes is an irreversible action.",
                requires_confirmation=True,
                confirmation_prompt="Are you certain you wish to delete all saved notes permanently?"
            )
        count = self.memory.clear_all_notes()
        self.memory.log_action("clear_all_notes", "notes_table", "success", f"Cleared {count} notes")
        return ActionResult(success=True, message=f"Successfully purged {count} notes from local memory.")

    def _handle_diagnostics(self, **kw) -> ActionResult:
        diag = get_system_diagnostics()
        pkgs = ", ".join([f"{k}: {v}" for k, v in diag.get("packages", {}).items()])
        msg = (
            f"JARVIS System Diagnostics:\n"
            f"• OS: {diag.get('os')} {diag.get('os_release')} ({diag.get('architecture')})\n"
            f"• Python: {diag.get('python_version')}\n"
            f"• Packages: {pkgs}\n"
            f"• Audio: {diag.get('audio_devices_count', 0)} devices detected (Default In: {diag.get('default_input_device')})"
        )
        return ActionResult(success=True, message=msg, data=diag)

    def _handle_set_language(self, language: str = "", **kw) -> ActionResult:
        code = language_registry.resolve_language(language, fallback="")
        if not code:
            supported = ", ".join([s.display_name for s in language_registry.all_languages()])
            return ActionResult(
                success=False,
                message=f"Unknown language '{language}'. Supported languages: {supported}."
            )
        spec = language_registry.get(code)
        self.memory.set_setting("preferred_response_language", code)
        return ActionResult(
            success=True,
            message=f"Preferred response language updated to {spec.display_name} ({spec.native_name}).",
            data={"language_code": code, "language_name": spec.display_name}
        )

    def _handle_translate(self, text: str = "", target_language: str = "en", **kw) -> ActionResult:
        code = language_registry.resolve_language(target_language, fallback="en")
        spec = language_registry.get(code)
        lang_name = spec.display_name if spec else "English"
        return ActionResult(
            success=True,
            message=f"Translation request to {lang_name} ({code}) for: '{text}'",
            data={"text": text, "target_language": code, "language_name": lang_name}
        )

    def route(self, text: str, confirmed: bool = False) -> Optional[ActionResult]:
        """Matches input text across 10 languages and mixed dialects to a registered command."""
        query = text.strip()
        low = query.lower()
        if not low:
            return None

        # 1. Set language pattern: "set language to <x>", "switch to <x>", "tamil-la pesu"
        set_lang_m = re.match(r"^(?:set|change|switch)\s+(?:the\s+)?(?:response\s+)?language\s+(?:to|into)\s+([a-zA-Z]+)", low)
        if not set_lang_m:
            set_lang_m = re.match(r"^switch\s+to\s+([a-zA-Z]+)$", low)
        if not set_lang_m:
            set_lang_m = re.match(r"^(tamil|hindi|telugu|malayalam|kannada|german|french|spanish|japanese|english)(?:-la\s+pesu|\s+mein\s+bolo|-lo\s+matladu|-il\s+samsaricku|-dalli\s+maathadu|\s+sprechen|\s+parler|\s+hablar)$", low)
        if set_lang_m:
            target_lang = set_lang_m.group(1).strip()
            cmd = self.registry.get("set_language")
            if cmd:
                res = cmd.handler(language=target_lang)
                if res and not res.intent:
                    res.intent = cmd.intent
                return res

        # 2. Translation pattern: "translate <text> to/into <lang>"
        trans_m = re.match(r"^(?:please\s+)?translate\s+['\"]?(.+?)['\"]?\s+(?:to|into|in)\s+([a-zA-Z]+)$", low)
        if trans_m:
            phrase_to_trans = query[trans_m.start(1):trans_m.end(1)].strip()
            target_lang = trans_m.group(2).strip()
            cmd = self.registry.get("translate_text")
            if cmd:
                res = cmd.handler(text=phrase_to_trans, target_language=target_lang)
                if res and not res.intent:
                    res.intent = cmd.intent
                return res

        # 3. Check for save note pattern: "remember that ...", "note that ...", etc.
        save_patterns = [
            r"^(?:please\s+)?remember\s+(?:that\s+)?(.+)",
            r"^(?:please\s+)?note\s+(?:that\s+)?(.+)",
            r"^save\s+(?:a\s+)?note\s+(?:that\s+)?(.+)",
            r"^(?:idhai\s+)?note\s+pannu\s+(.+)",
            r"^yaad\s+rakho\s+(?:ki\s+)?(.+)",
            r"^merk\s+dir\s+(?:dass\s+)?(.+)",
            r"^idi\s+gurtupettuko\s+(.+)",
            r"^ithu\s+ormakkuka\s+(.+)",
            r"^idannu\s+nenapidi\s+(.+)",
        ]
        for pat in save_patterns:
            m = re.match(pat, low, re.IGNORECASE)
            if m:
                note_content = query[m.start(1):m.end(1)].strip()
                cmd = self.registry.get("save_note")
                if cmd:
                    res = cmd.handler(content=note_content)
                    if res and not res.intent:
                        res.intent = cmd.intent
                    return res
                return None

        # 4. Search notes pattern: "search notes for <x>", "find note <x>"
        search_m = re.match(r"^(?:search|find)\s+(?:my\s+)?notes?\s+(?:for\s+)?(.+)", low)
        if search_m:
            term = search_m.group(1).strip()
            results = self.memory.search_notes(term)
            if not results:
                return ActionResult(success=True, message=f"No notes found matching '{term}'.", intent="search_notes")
            formatted = "\n".join([f"• [{n['id']}] {n['note']}" for n in results[:10]])
            return ActionResult(
                success=True,
                message=f"Found {len(results)} note(s) matching '{term}':\n{formatted}",
                intent="search_notes",
                data={"results": results}
            )

        # 5. Search files pattern: "search file <query>", "find file <query>", "file thedu <query>"
        search_f_m = re.match(r"^(?:search|find|locate)\s+(?:for\s+)?(?:the\s+)?files?\s+['\"]?(.+?)['\"]?$", low)
        if not search_f_m:
            search_f_m = re.match(r"^files?\s+(?:thedu|dhoondho|search\s+pannu|search\s+karo)\s+['\"]?(.+?)['\"]?$", low)
        if search_f_m:
            f_term = search_f_m.group(1).strip()
            return self._handle_search_files(f_term)

        # 6. Open Folder pattern: "open downloads folder", "downloads folder open pannu"
        folder_m = re.match(r"^(?:open|show)\s+(?:the\s+)?(downloads|documents|desktop|pictures|photos|music|videos|home)\s*(?:folder)?$", low)
        if not folder_m:
            folder_m = re.match(r"^(downloads|documents|desktop|pictures|photos|music|videos|home)\s*(?:folder\s*)?(?:open\s+pannu|kholo|open\s+cheyi|thurakku|there)$", low)
        if folder_m:
            target_alias = folder_m.group(1).strip()
            return self._handle_open_folder(target_alias)

        # 7. Dynamic App Launch: "open <app>", "<app> open pannu", "<app> kholo", "öffne <app>"
        app_open_m = re.match(r"^(?:open|launch|start|run)\s+([a-zA-Z\s]+)$", low)
        if not app_open_m:
            app_open_m = re.match(r"^([a-zA-Z\s]+)\s+(?:open\s+pannu|kholo|open\s+karo|open\s+cheyi|thurakku|open\s+maadu|öffnen)$", low)
        if not app_open_m:
            app_open_m = re.match(r"^(?:öffne|ouvre|abre)\s+([a-zA-Z\s]+)$", low)
        if app_open_m:
            candidate_app = app_open_m.group(1).strip().lower()
            if candidate_app in config.approved_apps:
                res = self.actions.launch_app(candidate_app)
                return ActionResult(success=res["success"], message=res["message"], intent=f"open_{candidate_app}")

        # 8. Match against registered multilingual examples
        for cmd in self.registry.all_commands():
            for lang, examples in cmd.multilingual_examples.items():
                for ex in examples:
                    ex_clean = ex.lower().replace("<query>", "").replace("<text>", "").replace("<lang>", "").strip()
                    if not ex_clean:
                        continue
                    # Match exact or clean containment
                    if low == ex_clean or (len(ex_clean) > 4 and ex_clean in low):
                        logger.info(f"Matched intent '{cmd.intent}' via example '{ex}' in language '{lang}'")
                        res = cmd.handler(confirmed=confirmed)
                        if res and not res.intent:
                            res.intent = cmd.intent
                        return res

        return None
