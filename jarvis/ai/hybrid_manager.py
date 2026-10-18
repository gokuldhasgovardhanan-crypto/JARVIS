from typing import List, Dict, Optional
from jarvis.ai.base import BaseAIProvider, AIResponse
from jarvis.ai.cloud_provider import CloudAIProvider
from jarvis.ai.local_provider import LocalAIProvider
from jarvis.utils.logging_config import logger


class HybridAIManager:
    """Orchestrates cloud and local AI providers with automated resilience fallback."""

    def __init__(
        self,
        cloud_provider: Optional[BaseAIProvider] = None,
        local_provider: Optional[BaseAIProvider] = None,
    ):
        self.cloud = cloud_provider or CloudAIProvider()
        self.local = local_provider or LocalAIProvider()

    def generate(
        self,
        messages: List[Dict[str, str]],
        target_language: str = "en",
    ) -> AIResponse:
        """Attempts Cloud AI; falls back seamlessly to Local AI upon failure."""
        if self.cloud.is_available():
            logger.info("Routing query to Cloud AI provider...")
            response = self.cloud.generate(messages, target_language)
            if response.success:
                return response
            
            logger.warning(
                f"Cloud AI call failed ({response.error_message}). Initiating fallback to Local AI..."
            )

        # Fallback to Local AI
        logger.info("Routing query to Local AI provider...")
        return self.local.generate(messages, target_language)

    def get_status(self) -> Dict[str, Any]:
        return {
            "cloud_available": self.cloud.is_available(),
            "cloud_provider": self.cloud.get_provider_name(),
            "local_provider": self.local.get_provider_name(),
        }
