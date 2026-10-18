from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Any


@dataclass
class AIResponse:
    text: str
    success: bool
    provider_name: str
    language: str = "en"
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAIProvider(ABC):
    """Abstract interface for all JARVIS conversational AI providers."""

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        target_language: str = "en",
    ) -> AIResponse:
        """Generates conversational response maintaining context and target language."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is configured and reachable."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns identifier name of the provider."""
        pass
