from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any


@dataclass
class ActionResult:
    success: bool
    message: str
    intent: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    requires_confirmation: bool = False
    confirmation_prompt: Optional[str] = None



@dataclass
class Command:
    intent: str
    description: str
    handler: Callable[..., ActionResult]
    multilingual_examples: Dict[str, List[str]] = field(default_factory=dict)
    is_sensitive: bool = False
    parameters_schema: Dict[str, Any] = field(default_factory=dict)


class CommandRegistry:
    """Central registry for registered voice and text commands."""

    def __init__(self):
        self._commands: Dict[str, Command] = {}

    def register(self, command: Command) -> None:
        self._commands[command.intent] = command

    def get(self, intent: str) -> Optional[Command]:
        return self._commands.get(intent)

    def all_commands(self) -> List[Command]:
        return list(self._commands.values())

    def get_help_summary(self, language: str = "en") -> str:
        """Returns human-readable command list."""
        lines = ["Available Commands:"]
        for cmd in self._commands.values():
            sample = cmd.multilingual_examples.get(language, cmd.multilingual_examples.get("en", []))
            sample_str = f" (e.g., '{sample[0]}')" if sample else ""
            lines.append(f"• {cmd.intent}: {cmd.description}{sample_str}")
        return "\n".join(lines)
