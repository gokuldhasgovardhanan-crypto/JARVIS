from typing import List, Dict, Optional
from jarvis.ai.base import BaseAIProvider, AIResponse
from jarvis.config import config
from jarvis.languages.policies import policy_engine
from jarvis.utils.logging_config import logger


class CloudAIProvider(BaseAIProvider):
    """Cloud-based conversational AI provider powered by OpenAI / compatible API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 12.0,
    ):
        self.api_key = (api_key or config.openai_api_key or "").strip()
        self.model = model or config.openai_model
        self.timeout = timeout
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        if not self.api_key:
            return
        try:
            from openai import OpenAI  # type: ignore
            self._client = OpenAI(api_key=self.api_key, timeout=self.timeout)
            logger.info(f"Initialized CloudAIProvider with model: {self.model}")
        except Exception as exc:
            logger.warning(f"Failed to initialize OpenAI client: {exc}")
            self._client = None

    def is_available(self) -> bool:
        return bool(self.api_key and self._client is not None)

    def get_provider_name(self) -> str:
        return f"Cloud AI ({self.model})"

    def generate(
        self,
        messages: List[Dict[str, str]],
        target_language: str = "en",
    ) -> AIResponse:
        """Sends chat completion request with strict language adherence system prompt."""
        if not self.is_available():
            return AIResponse(
                text="Cloud AI is not configured. Please supply an API key in the .env file.",
                success=False,
                provider_name=self.get_provider_name(),
                language=target_language,
                error_message="Missing or invalid API key",
            )

        lang_instruction = policy_engine.format_system_prompt_language_instruction(target_language)
        system_prompt = (
            "You are JARVIS, an advanced, concise personal desktop AI assistant for Windows 11. "
            "You are polite, precise, and highly competent. "
            f"{lang_instruction} "
            "Never claim to have executed computer actions unless they were actually performed. "
            "Never invent file paths or sensitive system changes."
        )

        full_messages = [{"role": "system", "content": system_prompt}] + messages[-8:]

        try:
            assert self._client is not None
            response = self._client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=0.7,
                max_tokens=600,
            )
            answer = response.choices[0].message.content or ""
            return AIResponse(
                text=answer.strip(),
                success=True,
                provider_name=self.get_provider_name(),
                language=target_language,
            )

        except Exception as exc:
            err_str = str(exc)
            logger.error(f"Cloud AI error during generation: {err_str}", exc_info=False)
            
            # Categorize user-friendly messages without exposing raw tokens/keys
            friendly_err = "I could not connect to the cloud AI service."
            if "Authentication" in err_str or "401" in err_str:
                friendly_err = "Cloud AI authentication failed. Please verify your OPENAI_API_KEY in the .env file."
            elif "Rate limit" in err_str or "429" in err_str:
                friendly_err = "Cloud AI rate limit reached. Please wait a moment before trying again."
            elif "timeout" in err_str.lower():
                friendly_err = "Cloud AI request timed out. Operating in offline fallback mode."

            return AIResponse(
                text=friendly_err,
                success=False,
                provider_name=self.get_provider_name(),
                language=target_language,
                error_message=err_str,
            )
