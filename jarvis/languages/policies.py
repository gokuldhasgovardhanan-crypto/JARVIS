from dataclasses import dataclass
from typing import Optional, Tuple
from jarvis.languages.registry import language_registry, LanguageSpec
from jarvis.utils.logging_config import logger


@dataclass
class LanguagePolicyDecision:
    detected_language: str
    response_language: str
    is_fallback: bool
    reason: str


class LanguagePolicyEngine:
    """Enforces language selection, fallback rules, and mixed-language consistency."""

    def __init__(self, default_language: str = "en"):
        self.default_language = default_language

    def determine_response_language(
        self,
        detected_language: str,
        user_preference: Optional[str] = None,
        confidence: float = 1.0,
    ) -> LanguagePolicyDecision:
        """
        Determines the appropriate response language based on user preference,
        detected language, confidence threshold, and registered capabilities.
        """
        # 1. Explicit user override / configured preference
        if user_preference and user_preference != "auto":
            resolved_pref = language_registry.resolve_language(user_preference, fallback="en")
            return LanguagePolicyDecision(
                detected_language=detected_language,
                response_language=resolved_pref,
                is_fallback=False,
                reason=f"User explicit preference override: {resolved_pref}",
            )

        # 2. Check confidence threshold
        if confidence < 0.45:
            logger.info(f"Low language detection confidence ({confidence:.2f}). Falling back to default: {self.default_language}")
            return LanguagePolicyDecision(
                detected_language=detected_language,
                response_language=self.default_language,
                is_fallback=True,
                reason=f"Low detection confidence ({confidence:.2f}); falling back to default.",
            )

        # 3. Check if detected language is in supported 10 languages
        resolved = language_registry.resolve_language(detected_language, fallback=self.default_language)
        return LanguagePolicyDecision(
            detected_language=detected_language,
            response_language=resolved,
            is_fallback=(resolved != detected_language and detected_language != "en"),
            reason=f"Matched detected language: {resolved}",
        )

    def format_system_prompt_language_instruction(self, response_language_code: str) -> str:
        """Generates dynamic system prompt instruction guaranteeing response language consistency."""
        spec: Optional[LanguageSpec] = language_registry.get(response_language_code)
        lang_name = spec.display_name if spec else "English"
        native_name = spec.native_name if spec else "English"

        return (
            f"MANDATORY LANGUAGE RULE: You MUST compose your entire response in {lang_name} ({native_name}). "
            "Do NOT switch to another language mid-response. "
            "Preserve code snippets, technical terms, software names (e.g. 'Notepad', 'Calculator'), "
            "proper nouns, and URLs in their original standard form."
        )


policy_engine = LanguagePolicyEngine()
