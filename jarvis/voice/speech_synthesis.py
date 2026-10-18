import threading
import queue
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable, Any
from jarvis.config import config
from jarvis.languages.registry import language_registry
from jarvis.utils.logging_config import logger


@dataclass
class VoiceCapability:
    id: str
    name: str
    language_code: str
    gender: str = "Unknown"
    is_local: bool = True
    provider: str = "Windows SAPI5"


class BaseTTSProvider(ABC):
    """Abstract interface for text-to-speech providers."""

    @abstractmethod
    def speak(
        self,
        text: str,
        language_code: str = "en",
        rate: int = 175,
        volume: float = 1.0,
        on_done: Optional[Callable[[], None]] = None,
    ) -> bool:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def get_available_voices(self) -> List[VoiceCapability]:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass


class LocalSapiTTSProvider(BaseTTSProvider):
    """Local Windows SAPI5 text-to-speech provider via pyttsx3."""

    def __init__(self):
        self._lock = threading.Lock()
        self._current_engine = None
        self._is_speaking = False
        self._voices_cache: Optional[List[VoiceCapability]] = None

    def is_available(self) -> bool:
        try:
            import pyttsx3  # type: ignore
            return True
        except ImportError:
            return False

    def get_available_voices(self) -> List[VoiceCapability]:
        if self._voices_cache is not None:
            return self._voices_cache

        voices_list: List[VoiceCapability] = []
        if not self.is_available():
            return voices_list

        try:
            import pyttsx3  # type: ignore
            engine = pyttsx3.init()
            raw_voices = engine.getProperty("voices") or []
            for v in raw_voices:
                name_low = (v.name or "").lower()
                lang_code = "en"
                # Determine language code from voice name or ID
                for code in language_registry.supported_codes():
                    spec = language_registry.get(code)
                    if spec and (spec.display_name.lower() in name_low or code in name_low):
                        lang_code = code
                        break

                gender = "Female" if "female" in name_low or "zira" in name_low else "Male"
                voices_list.append(
                    VoiceCapability(
                        id=v.id,
                        name=v.name,
                        language_code=lang_code,
                        gender=gender,
                        is_local=True,
                        provider="Windows SAPI5",
                    )
                )
            engine.stop()
        except Exception as exc:
            logger.warning(f"Error enumerating local SAPI voices: {exc}")

        self._voices_cache = voices_list
        return voices_list

    def find_voice_for_language(self, language_code: str) -> Optional[VoiceCapability]:
        """Finds a matching local voice for the target language."""
        voices = self.get_available_voices()
        for v in voices:
            if v.language_code == language_code:
                return v
        return None

    def speak(
        self,
        text: str,
        language_code: str = "en",
        rate: int = 175,
        volume: float = 1.0,
        on_done: Optional[Callable[[], None]] = None,
    ) -> bool:
        clean_text = text.strip()
        if not clean_text or not self.is_available():
            if on_done:
                on_done()
            return False

        # Find voice for language
        voice = self.find_voice_for_language(language_code)
        # If no local voice exists for this language (e.g. Tamil on standard US Windows),
        # do NOT speak with wrong accent if user asked for authentic language output
        if not voice and language_code != "en":
            logger.info(f"No local SAPI voice installed for language: {language_code}")
            if on_done:
                on_done()
            return False

        def worker():
            with self._lock:
                try:
                    import pyttsx3  # type: ignore
                    self._is_speaking = True
                    engine = pyttsx3.init()
                    self._current_engine = engine

                    engine.setProperty("rate", rate)
                    engine.setProperty("volume", max(0.0, min(1.0, volume)))
                    if voice:
                        engine.setProperty("voice", voice.id)

                    engine.say(clean_text)
                    engine.runAndWait()
                    engine.stop()
                except Exception as exc:
                    logger.error(f"SAPI TTS error: {exc}", exc_info=True)
                finally:
                    self._is_speaking = False
                    self._current_engine = None
                    if on_done:
                        on_done()

        threading.Thread(target=worker, daemon=True, name="TTSWorker").start()
        return True

    def stop(self) -> None:
        """Interrupts active speech synthesis."""
        if self._current_engine and self._is_speaking:
            try:
                self._current_engine.stop()
                logger.info("Speech synthesis stopped by user interrupt.")
            except Exception:
                pass


class CloudTTSProvider(BaseTTSProvider):
    """High-fidelity multilingual Cloud TTS adapter using OpenAI Audio Speech."""

    def __init__(self, api_key: Optional[str] = None):
        if api_key is not None:
            self.api_key = api_key.strip()
        else:
            self.api_key = (config.openai_api_key or "").strip()
        self._client = None
        self._is_speaking = False
        if self.api_key:
            try:
                from openai import OpenAI  # type: ignore
                self._client = OpenAI(api_key=self.api_key, timeout=12.0)
            except Exception:
                self._client = None

    def is_available(self) -> bool:
        return bool(self.api_key and self._client is not None)

    def get_available_voices(self) -> List[VoiceCapability]:
        voices = ["alloy", "nova", "shimmer", "echo", "fable", "onyx"]
        return [
            VoiceCapability(
                id=v,
                name=f"OpenAI {v.capitalize()}",
                language_code="multilingual",
                is_local=False,
                provider="OpenAI Cloud TTS",
            )
            for v in voices
        ]

    def speak(
        self,
        text: str,
        language_code: str = "en",
        rate: int = 175,
        volume: float = 1.0,
        on_done: Optional[Callable[[], None]] = None,
    ) -> bool:
        if not self.is_available():
            if on_done:
                on_done()
            return False

        spec = language_registry.get(language_code)
        voice_name = spec.cloud_voice_name if spec else "alloy"

        def worker():
            try:
                assert self._client is not None
                import sounddevice as sd  # type: ignore
                import soundfile as sf   # type: ignore
                import io

                self._is_speaking = True
                response = self._client.audio.speech.create(
                    model="tts-1",
                    voice=voice_name,
                    input=text[:500],  # Clamp length for performance
                )
                audio_bytes = response.content
                data, fs = sf.read(io.BytesIO(audio_bytes))
                sd.play(data * volume, fs)
                sd.wait()
            except Exception as exc:
                logger.warning(f"Cloud TTS playback failed: {exc}")
            finally:
                self._is_speaking = False
                if on_done:
                    on_done()

        threading.Thread(target=worker, daemon=True, name="CloudTTSWorker").start()
        return True

    def stop(self) -> None:
        try:
            import sounddevice as sd  # type: ignore
            sd.stop()
        except Exception:
            pass


class TTSManager:
    """Orchestrates text-to-speech with capability table and fallback to text."""

    def __init__(
        self,
        local_provider: Optional[BaseTTSProvider] = None,
        cloud_provider: Optional[BaseTTSProvider] = None,
    ):
        self.local = local_provider or LocalSapiTTSProvider()
        self.cloud = cloud_provider or CloudTTSProvider()
        self.prefer_local = True

    def speak(
        self,
        text: str,
        language_code: str = "en",
        rate: int = 175,
        volume: float = 1.0,
        on_done: Optional[Callable[[], None]] = None,
    ) -> bool:
        # 1. Try local voice if available for requested language
        if self.prefer_local and self.local.is_available():
            success = self.local.speak(text, language_code, rate, volume, on_done)
            if success:
                return True

        # 2. Try cloud voice
        if self.cloud.is_available():
            logger.info(f"Using Cloud TTS for {language_code} voice output...")
            return self.cloud.speak(text, language_code, rate, volume, on_done)

        # 3. Fallback to silent text (never speak with wrong language voice)
        logger.info(f"No compatible voice for '{language_code}'. Falling back to text console.")
        if on_done:
            on_done()
        return False

    def stop(self) -> None:
        self.local.stop()
        self.cloud.stop()

    def get_capability_table(self) -> Dict[str, Any]:
        """Returns voice status report across all 10 target languages."""
        table: Dict[str, Any] = {}
        for spec in language_registry.all_languages():
            has_local = False
            if isinstance(self.local, LocalSapiTTSProvider):
                has_local = self.local.find_voice_for_language(spec.code) is not None

            table[spec.code] = {
                "display_name": spec.display_name,
                "local_voice_available": has_local,
                "cloud_voice_available": self.cloud.is_available(),
                "cloud_voice_name": spec.cloud_voice_name,
            }
        return table
