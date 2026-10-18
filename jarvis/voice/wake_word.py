import threading
import time
import numpy as np
from typing import Callable, Optional, Dict, Any
from jarvis.config import config
from jarvis.utils.logging_config import logger


class WakeWordEngine:
    """
    Dedicated local wake-word detection engine with self-trigger suppression,
    cooldown debouncing, and continuous microphone monitoring outside the UI thread.
    """

    def __init__(
        self,
        wake_phrase: Optional[str] = None,
        on_wake_detected: Optional[Callable[[], None]] = None,
        on_level: Optional[Callable[[float], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        threshold: float = 0.5,
        debounce_seconds: float = 2.0,
    ):
        self.wake_phrase = (wake_phrase or config.wake_phrase or "hey jarvis").lower().strip()
        self.on_wake_detected = on_wake_detected
        self.on_level = on_level
        self.on_status = on_status
        self.on_error = on_error
        self.threshold = threshold
        self.debounce_seconds = debounce_seconds

        self.is_running = False
        self._is_speaking = False  # Echo suppression flag
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._last_trigger_time: float = 0.0

        # Attempt to load openWakeWord model
        self._oww_model = None
        self._use_oww = self._init_openwakeword()

    def _init_openwakeword(self) -> bool:
        """Attempts to initialize openWakeWord model if installed."""
        try:
            import openwakeword  # type: ignore
            from openwakeword.model import Model  # type: ignore

            # Search for hey_jarvis or default models
            try:
                self._oww_model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
                logger.info("Loaded openWakeWord model for 'hey_jarvis'.")
                return True
            except Exception:
                # Fallback to downloading or standard models
                openwakeword.utils.download_models()
                self._oww_model = Model(inference_framework="onnx")
                logger.info("Loaded openWakeWord default model library.")
                return True
        except Exception as exc:
            logger.info(f"openWakeWord not loaded ({exc}). Using energy-gated phrase spotter fallback.")
            self._oww_model = None
            return False

    def set_speaking_state(self, is_speaking: bool) -> None:
        """
        Suppresses wake-word detection while JARVIS is speaking to prevent
        accidental self-triggering from speaker audio.
        """
        self._is_speaking = is_speaking
        if is_speaking:
            logger.debug("Wake-word listener muted (assistant is speaking).")
        else:
            logger.debug("Wake-word listener unmuted.")

    def start(self, device_index: Optional[int] = None) -> bool:
        """Starts continuous wake-word listening in a background thread."""
        if self.is_running:
            return True

        self._stop_event.clear()
        self.is_running = True

        self._worker_thread = threading.Thread(
            target=self._listen_loop,
            args=(device_index,),
            daemon=True,
            name="WakeWordWorker",
        )
        self._worker_thread.start()
        if self.on_status:
            self.on_status(f"Listening for '{self.wake_phrase}'...")
        return True

    def stop(self) -> None:
        """Stops continuous wake-word listening."""
        self.is_running = False
        self._stop_event.set()
        if self.on_status:
            self.on_status("Wake-word listener paused.")

    def _listen_loop(self, device_index: Optional[int]) -> None:
        """Background continuous audio streaming loop."""
        sample_rate = 16000
        chunk_size = 1280  # 80ms chunks at 16kHz
        try:
            import sounddevice as sd  # type: ignore

            def audio_callback(indata, frames, time_info, status):
                if status and self.on_error:
                    self.on_error(f"Audio buffer overflow: {status}")

                if self._stop_event.is_set():
                    return

                # Compute volume level for HUD animation
                rms = np.sqrt(np.mean(indata**2))
                norm_level = min(1.0, float(rms * 10.0))
                if self.on_level:
                    self.on_level(norm_level)

                # Skip wake-word processing if assistant is speaking (echo suppression)
                if self._is_speaking:
                    return

                # Convert to 16-bit PCM integer
                audio_chunk = (indata * 32767).astype(np.int16).flatten()

                # 1. Primary: openWakeWord prediction
                if self._use_oww and self._oww_model:
                    try:
                        prediction = self._oww_model.predict(audio_chunk)
                        for model_name, score in prediction.items():
                            if score >= self.threshold:
                                self._trigger_wake_word(f"openWakeWord [{model_name} score={score:.2f}]")
                                return
                    except Exception as exc:
                        logger.debug(f"Prediction error: {exc}")

                # 2. Resilient Fallback: Energy-based voice detection trigger
                # When openWakeWord is not yet calibrated, audio activity triggers prompt
                elif not self._use_oww and norm_level > 0.35:
                    self._trigger_wake_word(f"Voice Activity [{norm_level:.2f}]")

            with sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                device=device_index,
                blocksize=chunk_size,
                dtype="float32",
                callback=audio_callback,
            ):
                logger.info(f"Continuous wake-word monitor active on device: {device_index}")
                while not self._stop_event.is_set():
                    time.sleep(0.05)

        except Exception as exc:
            self.is_running = False
            err = f"Wake-word audio stream error: {exc}"
            logger.error(err, exc_info=True)
            if self.on_error:
                self.on_error(err)
        finally:
            self.is_running = False
            logger.info("Wake-word monitor cleanly terminated.")

    def _trigger_wake_word(self, source_info: str) -> None:
        """Debounces and notifies subscribers of wake-word detection."""
        now = time.time()
        if (now - self._last_trigger_time) < self.debounce_seconds:
            # Within debounce window, ignore duplicate
            return

        self._last_trigger_time = now
        logger.info(f"Wake word '{self.wake_phrase}' detected via {source_info}!")
        if self.on_status:
            self.on_status("Wake word detected! Listening for command...")
        if self.on_wake_detected:
            self.on_wake_detected()
