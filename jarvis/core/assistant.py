from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from jarvis.config import config
from jarvis.memory.repository import MemoryRepository
from jarvis.automation.windows_actions import WindowsActionRunner
from jarvis.core.intent_router import IntentRouter
from jarvis.core.command_registry import ActionResult
from jarvis.core.conversation_manager import ConversationManager
from jarvis.languages.registry import language_registry
from jarvis.languages.policies import policy_engine
from jarvis.voice.language_detection import LanguageDetectionService, LanguageDetectionResult
from jarvis.ai.hybrid_manager import HybridAIManager
from jarvis.ai.base import AIResponse
from jarvis.utils.logging_config import logger


@dataclass
class AssistantResponse:
    text: str
    action_result: Optional[ActionResult] = None
    requires_confirmation: bool = False
    confirmation_prompt: Optional[str] = None
    detected_language: str = "en"
    response_language: str = "en"
    provider_name: str = "Local Engine"


class JarvisAssistant:
    """Core JARVIS assistant orchestrator coordinating language policies, AI brain, and routing."""

    def __init__(
        self,
        memory_repo: Optional[MemoryRepository] = None,
        ai_manager: Optional[HybridAIManager] = None,
    ):
        self.memory = memory_repo or MemoryRepository()
        self.actions = WindowsActionRunner(self.memory)
        self.router = IntentRouter(self.memory, self.actions)
        self.conversation = ConversationManager(self.memory)
        self.detector = LanguageDetectionService(fallback_language=config.default_language)
        self.ai = ai_manager or HybridAIManager()
        self.pending_sensitive_action: Optional[str] = None

    def handle(
        self,
        text: str,
        detected_language: Optional[str] = None,
        preferred_response_language: Optional[str] = None,
        speech_metadata: Optional[Dict[str, Any]] = None,
    ) -> AssistantResponse:
        """Processes user input through language detection, intent routing, and hybrid AI."""
        query = text.strip()
        if not query:
            return AssistantResponse(
                text="I didn't catch that. Please state your command.",
                detected_language="en",
                response_language="en",
            )

        # 1. Multi-tier Language Detection
        if not detected_language or detected_language == "auto":
            # Retrieve last conversation turn language as weak prior
            last_turns = self.conversation.get_context_window()
            prev_lang = None
            if last_turns:
                prev_lang = self.memory.get_setting("last_detected_language")

            detection_res: LanguageDetectionResult = self.detector.detect(
                query, speech_metadata=speech_metadata, previous_language=prev_lang
            )
            detected_lang = detection_res.language
            conf = detection_res.confidence
        else:
            detected_lang = language_registry.resolve_language(detected_language, fallback="en")
            conf = 1.0

        self.memory.set_setting("last_detected_language", detected_lang)

        # 2. Determine Response Language via Policy Engine
        # Check if user stored preference in DB
        db_pref = self.memory.get_setting("preferred_response_language")
        effective_pref = preferred_response_language or db_pref or "auto"
        decision = policy_engine.determine_response_language(
            detected_language=detected_lang,
            user_preference=effective_pref,
            confidence=conf,
        )
        resp_lang = decision.response_language

        # Persist user turn
        self.conversation.add_user_message(query, detected_lang, resp_lang)

        # 3. Handle confirmation flow for pending sensitive action
        if self.pending_sensitive_action:
            low = query.lower()
            if low in {"yes", "confirm", "proceed", "y", "sure", "ok", "aam", "haan", "ja", "oui", "hai"}:
                pending_intent = self.pending_sensitive_action
                self.pending_sensitive_action = None
                cmd = self.router.registry.get(pending_intent)
                if cmd:
                    result = cmd.handler(confirmed=True)
                    self.conversation.add_assistant_message(result.message, resp_lang)
                    return AssistantResponse(
                        text=result.message,
                        action_result=result,
                        detected_language=detected_lang,
                        response_language=resp_lang,
                        provider_name="Local Command Gate",
                    )
            elif low in {"no", "cancel", "stop", "abort", "vendaam", "nahi", "nein", "non", "iie"}:
                self.pending_sensitive_action = None
                msg = "Operation canceled. No changes were made."
                self.conversation.add_assistant_message(msg, resp_lang)
                return AssistantResponse(
                    text=msg,
                    detected_language=detected_lang,
                    response_language=resp_lang,
                    provider_name="Local Command Gate",
                )

        # 4. Match against registered local commands
        action_result = self.router.route(query)
        if action_result:
            # Handle translation action specially if AI is available
            if action_result.intent == "translate_text" and action_result.data:
                trans_text = action_result.data.get("text", "")
                target_lang = action_result.data.get("target_language", "en")
                target_spec = language_registry.get(target_lang)
                target_name = target_spec.display_name if target_spec else target_lang

                ai_msg = [
                    {
                        "role": "user",
                        "content": f"Translate the following text accurately into {target_name}. Return ONLY the direct translation:\n{trans_text}",
                    }
                ]
                ai_resp = self.ai.generate(ai_msg, target_language=target_lang)
                final_text = f"Translation ({target_name}):\n{ai_resp.text}"
                self.conversation.add_assistant_message(final_text, target_lang)
                return AssistantResponse(
                    text=final_text,
                    action_result=action_result,
                    detected_language=detected_lang,
                    response_language=target_lang,
                    provider_name=ai_resp.provider_name,
                )

            # Sensitive action prompt
            if action_result.requires_confirmation:
                self.pending_sensitive_action = action_result.intent
                prompt = action_result.confirmation_prompt or action_result.message
                self.conversation.add_assistant_message(prompt, resp_lang)
                return AssistantResponse(
                    text=prompt,
                    action_result=action_result,
                    requires_confirmation=True,
                    confirmation_prompt=prompt,
                    detected_language=detected_lang,
                    response_language=resp_lang,
                    provider_name="Local Command Gate",
                )

            self.conversation.add_assistant_message(action_result.message, resp_lang)
            return AssistantResponse(
                text=action_result.message,
                action_result=action_result,
                detected_language=detected_lang,
                response_language=resp_lang,
                provider_name="Local Command Registry",
            )

        # 5. Hybrid AI Brain (Cloud -> Local Fallback)
        context_messages = self.conversation.get_context_window()
        ai_resp: AIResponse = self.ai.generate(context_messages, target_language=resp_lang)
        self.conversation.add_assistant_message(ai_resp.text, resp_lang)

        return AssistantResponse(
            text=ai_resp.text,
            detected_language=detected_lang,
            response_language=resp_lang,
            provider_name=ai_resp.provider_name,
        )
