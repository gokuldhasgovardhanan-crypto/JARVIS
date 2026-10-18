from typing import List, Dict, Optional
import urllib.request
import json
from jarvis.ai.base import BaseAIProvider, AIResponse
from jarvis.config import config
from jarvis.languages.registry import language_registry, LanguageSpec
from jarvis.languages.policies import policy_engine
from jarvis.utils.logging_config import logger


class LocalAIProvider(BaseAIProvider):
    """
    Offline local AI provider. Connects to local endpoint (e.g. Ollama)
    if active, or provides structured offline multilingual fallback responses.
    """

    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or config.local_ai_endpoint
        self._local_server_active = self._check_endpoint()

    def _check_endpoint(self) -> bool:
        """Probes local Ollama / local LLM server with 1s timeout."""
        try:
            req = urllib.request.Request(f"{self.endpoint}/models", method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    def is_available(self) -> bool:
        return True  # Rule-based fallback is always available offline

    def get_provider_name(self) -> str:
        return "Local LLM (Ollama)" if self._local_server_active else "Local Offline Engine"

    def generate(
        self,
        messages: List[Dict[str, str]],
        target_language: str = "en",
    ) -> AIResponse:
        """Generates response via local Ollama server or built-in offline rules."""
        if not messages:
            return AIResponse(
                text="Awaiting query.",
                success=True,
                provider_name=self.get_provider_name(),
                language=target_language,
            )

        last_user_message = messages[-1].get("content", "").strip()

        # If local Ollama daemon is detected
        if self._local_server_active:
            try:
                lang_instruction = policy_engine.format_system_prompt_language_instruction(target_language)
                payload = {
                    "model": "llama3.2:latest",
                    "messages": [
                        {"role": "system", "content": f"You are JARVIS. {lang_instruction}"}
                    ] + messages[-6:],
                    "temperature": 0.7,
                }
                req = urllib.request.Request(
                    f"{self.endpoint}/chat/completions",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    answer = data["choices"][0]["message"]["content"]
                    return AIResponse(
                        text=answer.strip(),
                        success=True,
                        provider_name=self.get_provider_name(),
                        language=target_language,
                    )
            except Exception as exc:
                logger.warning(f"Local Ollama server call failed: {exc}")
                self._local_server_active = False

        # Built-in offline multilingual response
        spec = language_registry.get(target_language)
        lang_name = spec.display_name if spec else "English"

        offline_templates = {
            "en": (
                f"JARVIS Local Engine active (Offline Mode). "
                f"I processed your query in {lang_name}. Cloud AI is currently disconnected, "
                "but all local Windows commands (Notepad, Calculator, Notes, Time, Diagnostics) are fully functional."
            ),
            "ta": (
                "JARVIS உள்ளூர் இயங்குதளம் செயலில் உள்ளது. இணைய இணைப்பு இல்லாதபோதும், "
                "நோட்பேட், கால்குலேட்டர், குறிப்புகள் மற்றும் கணினி நேரம் போன்ற அனைத்து உள்ளூர் கட்டளைகளும் செயல்படுகின்றன."
            ),
            "hi": (
                "जार्विस स्थानीय प्रणाली सक्रिय है। ऑनलाइन एआई कनेक्ट नहीं है, "
                "लेकिन नोटपैड, कैलकुलेटर, नोट्स और समय जैसी स्थानीय कमांड्स पूरी तरह काम कर रही हैं।"
            ),
            "de": (
                "Lokales JARVIS-System aktiv (Offline-Modus). "
                "Cloud-KI ist nicht konfiguriert, aber alle lokalen Befehle (Notizblock, Rechner, Notizen, Uhrzeit) funktionieren einwandfrei."
            ),
            "fr": (
                "Système local JARVIS actif (Mode hors ligne). "
                "L'IA cloud n'est pas connectée, mais toutes les commandes locales Windows restent opérationnelles."
            ),
            "es": (
                "Sistema local JARVIS activo (Modo sin conexión). "
                "La IA en la nube no está conectada, pero todos los comandos locales de Windows funcionan correctamente."
            ),
            "ja": (
                "JARVIS ローカルシステムが稼働しています（オフラインモード）。"
                "クラウドAIは接続されていませんが、メモ帳、計算機、メモ機能などのローカルコマンドは正常に機能します。"
            ),
        }

        resp_text = offline_templates.get(target_language, offline_templates["en"])
        return AIResponse(
            text=resp_text,
            success=True,
            provider_name=self.get_provider_name(),
            language=target_language,
            metadata={"offline_mode": True},
        )
