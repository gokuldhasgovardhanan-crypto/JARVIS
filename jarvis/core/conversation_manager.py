import uuid
from typing import List, Dict, Any
from jarvis.memory.repository import MemoryRepository
from jarvis.utils.logging_config import logger


class ConversationManager:
    """Manages active conversation session state and message history buffer."""

    def __init__(self, memory_repo: MemoryRepository, max_context_messages: int = 10):
        self.memory = memory_repo
        self.session_id = str(uuid.uuid4())
        self.max_context_messages = max_context_messages
        self._local_history: List[Dict[str, str]] = []

    def add_user_message(
        self,
        content: str,
        detected_language: str = "en",
        response_language: str = "en",
    ) -> None:
        """Records an incoming user message."""
        self._local_history.append({"role": "user", "content": content})
        try:
            self.memory.add_conversation_turn(
                session_id=self.session_id,
                role="user",
                content=content,
                detected_language=detected_language,
                response_language=response_language,
            )
        except Exception as exc:
            logger.warning(f"Failed to persist user message in SQLite: {exc}")

    def add_assistant_message(
        self,
        content: str,
        response_language: str = "en",
    ) -> None:
        """Records an outgoing assistant response."""
        self._local_history.append({"role": "assistant", "content": content})
        try:
            self.memory.add_conversation_turn(
                session_id=self.session_id,
                role="assistant",
                content=content,
                detected_language=response_language,
                response_language=response_language,
            )
        except Exception as exc:
            logger.warning(f"Failed to persist assistant message in SQLite: {exc}")

    def get_context_window(self) -> List[Dict[str, str]]:
        """Returns the recent conversation turns bounded by max_context_messages."""
        return self._local_history[-self.max_context_messages :]

    def clear(self) -> None:
        """Resets current in-memory history and creates a fresh session ID."""
        self._local_history.clear()
        self.session_id = str(uuid.uuid4())
        logger.info(f"Started new conversation session: {self.session_id}")
