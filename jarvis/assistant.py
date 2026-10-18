from datetime import datetime
import os
import subprocess
import webbrowser

from openai import OpenAI
from .config import OPENAI_API_KEY, OPENAI_MODEL
from .memory import MemoryStore


class JarvisAssistant:
    def __init__(self):
        self.memory = MemoryStore()
        self.client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        self.history = []

    def handle(self, text: str) -> str:
        command = text.strip()
        low = command.lower()

        if not command:
            return "I didn't catch that. Please try again."

        if low in {"help", "what can you do", "show commands"}:
            return (
                "You can ask me the time or date, open Notepad or Calculator, "
                "open YouTube or Google, or ask a question using the online AI brain."
            )

        if "what time" in low or low == "time":
            return "The time is " + datetime.now().strftime("%I:%M %p") + "."

        if "what date" in low or low == "date" or "today's date" in low:
            return "Today is " + datetime.now().strftime("%A, %B %d, %Y") + "."

        if "open notepad" in low:
            try:
                subprocess.Popen(["notepad.exe"])
                return "Opening Notepad."
            except Exception as exc:
                return f"I couldn't open Notepad: {exc}"

        if "open calculator" in low or "open calc" in low:
            try:
                subprocess.Popen(["calc.exe"])
                return "Opening Calculator."
            except Exception as exc:
                return f"I couldn't open Calculator: {exc}"

        if "open youtube" in low:
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube."

        if "open google" in low:
            webbrowser.open("https://www.google.com")
            return "Opening Google."

        if low.startswith("remember that "):
            note = command[len("remember that "):].strip()
            if note:
                self.memory.save_note(note)
                return "I'll keep that note in your local JARVIS memory."
            return "Tell me what you'd like me to remember."

        if low in {"show my notes", "read my notes", "what do you remember"}:
            notes = self.memory.get_notes()
            if not notes:
                return "Your local notes are empty."
            return "Here are your saved notes: " + " ; ".join(notes[:10])

        if not self.client:
            return (
                "My local command system is working, but online AI is not configured yet. "
                "Add your API key to the .env file to enable general AI conversations. "
                "Type 'help' to see available local commands."
            )

        try:
            self.history.append({"role": "user", "content": command})
            # Keep a short context window to control token use.
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are JARVIS, a helpful, concise desktop AI assistant. "
                        "Do not claim to have performed computer actions unless the local "
                        "command router actually performed them. Ask before suggesting "
                        "destructive or sensitive actions."
                    ),
                }
            ] + self.history[-10:]

            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
            )
            answer = response.choices[0].message.content or "I couldn't form a response."
            self.history.append({"role": "assistant", "content": answer})
            return answer
        except Exception as exc:
            return (
                "I couldn't reach the online AI service. Check your internet connection, "
                "API key, and model setting. Details: " + str(exc)
            )
