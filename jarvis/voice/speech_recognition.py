import os
import io
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from jarvis.config import config
from jarvis.languages.registry import language_registry
from jarvis.utils.logging_config import logger


@dataclass
class TranscriptionResult:
    text: str
    language: str = "en"
    probability: float = 1.0
    duration: float = 0.0
    is_local: bool = True
    provider_name: str = "Faster-Whisper (Local)"
    segments: List[Dict[str, Any]] = field(default_factory=list)


class BaseSTTProvider(ABC):
    """Abstract interface for speech transcription providers."""

    @abstractmethod
    def transcribe(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """Transcribes PCM audio bytes into text with detected language metadata."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class FasterWhisperSTTProvider(BaseSTTProvider):
    """Local offline speech recognition powered by Faster-Whisper (CTranslate2)."""

    def __init__(
        self,
        model_size: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: str = "default",
    ):
        self.model_size = model_size or config.whisper_model_size
        self.device = device or config.whisper_device
        self.compute_type = compute_type
        self._model = None
        self._is_loading = False

    def is_available(self) -> bool:
        try:
            import faster_whisper  # type: ignore
            return True
        except ImportError:
            return False

    def get_provider_name(self) -> str:
        return f"Faster-Whisper ({self.model_size}, {self.device})"

    def _ensure_model_loaded(self):
        if self._model is not None:
            return
        from faster_whisper import WhisperModel  # type: ignore

        logger.info(
            f"Loading Faster-Whisper model '{self.model_size}' on device '{self.device}'..."
        )
        # Store models under user data models dir
        download_root = str(config.models_dir / "whisper")
        self._model = WhisperModel(
            model_size_or_path=self.model_size,
            device=self.device,
            compute_type=self.compute_type,
            download_root=download_root,
        )
        logger.info(f"Faster-Whisper model '{self.model_size}' ready.")

    def transcribe(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        if not self.is_available():
            raise RuntimeError("faster_whisper package is not installed.")

        self._ensure_model_loaded()

        # Wrap PCM bytes into in-memory WAV container
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit PCM
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)
        wav_buffer.seek(0)

        assert self._model is not None
        # Normalize language parameter if specified, otherwise None for Whisper auto-detection
        whisper_lang = language if (language and language != "auto") else None

        segments, info = self._model.transcribe(
            wav_buffer,
            language=whisper_lang,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        text_pieces = []
        seg_list = []
        for segment in segments:
            text_pieces.append(segment.text)
            seg_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
            })

        full_text = " ".join(text_pieces).strip()
        detected_lang = language_registry.resolve_language(info.language, fallback="en")

        logger.info(
            f"Transcribed {info.duration:.1f}s audio: '{full_text}' (detected={detected_lang}, prob={info.language_probability:.2f})"
        )

        return TranscriptionResult(
            text=full_text,
            language=detected_lang,
            probability=float(info.language_probability),
            duration=float(info.duration),
            is_local=True,
            provider_name=self.get_provider_name(),
            segments=seg_list,
        )


class CloudSTTProvider(BaseSTTProvider):
    """Cloud speech-to-text adapter using OpenAI Whisper API."""

    def __init__(self, api_key: Optional[str] = None):
        if api_key is not None:
            self.api_key = api_key.strip()
        else:
            self.api_key = (config.openai_api_key or "").strip()
        self._client = None
        if self.api_key:
            try:
                from openai import OpenAI  # type: ignore
                self._client = OpenAI(api_key=self.api_key, timeout=15.0)
            except Exception:
                self._client = None

    def is_available(self) -> bool:
        return bool(self.api_key and self._client is not None)

    def get_provider_name(self) -> str:
        return "OpenAI Whisper (Cloud)"

    def transcribe(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        if not self.is_available():
            raise RuntimeError("Cloud STT is not configured (missing OPENAI_API_KEY).")

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)
        wav_buffer.seek(0)
        wav_buffer.name = "audio.wav"

        assert self._client is not None
        req_kwargs: Dict[str, Any] = {"model": "whisper-1", "file": wav_buffer}
        if language and language != "auto":
            req_kwargs["language"] = language

        transcript = self._client.audio.transcriptions.create(**req_kwargs)
        text = transcript.text.strip()

        return TranscriptionResult(
            text=text,
            language=language or "en",
            probability=0.95,
            duration=0.0,
            is_local=False,
            provider_name=self.get_provider_name(),
        )


class STTManager:
    """Manages active STT provider and falls back between local and cloud."""

    def __init__(
        self,
        local_provider: Optional[BaseSTTProvider] = None,
        cloud_provider: Optional[BaseSTTProvider] = None,
    ):
        self.local = local_provider or FasterWhisperSTTProvider()
        self.cloud = cloud_provider or CloudSTTProvider()
        self.prefer_local = True

    def transcribe(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        if self.prefer_local and self.local.is_available():
            try:
                return self.local.transcribe(audio_data, sample_rate, language)
            except Exception as exc:
                logger.warning(f"Local STT failed ({exc}). Attempting cloud fallback...")

        if self.cloud.is_available():
            return self.cloud.transcribe(audio_data, sample_rate, language)

        raise RuntimeError("No operational STT provider is available.")
