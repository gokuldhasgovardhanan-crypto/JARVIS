import threading
import time
import math
from dataclasses import dataclass
from typing import Callable, List, Optional, Dict, Any
from jarvis.utils.logging_config import logger


@dataclass
class AudioDeviceInfo:
    index: int
    name: str
    channels: int
    default_samplerate: int
    is_default: bool


class AudioInputService:
    """
    Microphone capture service with real-time level metering,
    energy-based voice endpointing, and audio device enumeration.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_duration_ms: int = 50,
        on_level: Optional[Callable[[float], None]] = None,
        on_speech_chunk: Optional[Callable[[bytes], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = int(sample_rate * (chunk_duration_ms / 1000.0))
        self.on_level = on_level
        self.on_speech_chunk = on_speech_chunk
        self.on_error = on_error

        self.is_recording = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._stream = None

    @staticmethod
    def get_input_devices() -> List[AudioDeviceInfo]:
        """Enumerates all available audio recording devices."""
        devices: List[AudioDeviceInfo] = []
        try:
            import sounddevice as sd  # type: ignore
            raw_devices = sd.query_devices()
            default_in = sd.default.device[0] if isinstance(sd.default.device, tuple) else sd.default.device

            for idx, dev in enumerate(raw_devices):
                if dev.get("max_input_channels", 0) > 0:
                    devices.append(
                        AudioDeviceInfo(
                            index=idx,
                            name=dev.get("name", f"Device #{idx}"),
                            channels=dev.get("max_input_channels", 1),
                            default_samplerate=int(dev.get("default_samplerate", 16000)),
                            is_default=(idx == default_in),
                        )
                    )
        except Exception as exc:
            logger.warning(f"Error enumerating audio devices: {exc}")
        return devices

    def start_recording(self, device_index: Optional[int] = None) -> bool:
        """Starts non-blocking microphone recording in a dedicated background worker."""
        if self.is_recording:
            return True

        self._stop_event.clear()
        self.is_recording = True

        self._thread = threading.Thread(
            target=self._record_worker,
            args=(device_index,),
            daemon=True,
            name="AudioInputWorker",
        )
        self._thread.start()
        return True

    def stop_recording(self) -> None:
        """Stops microphone recording."""
        self.is_recording = False
        self._stop_event.set()
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _record_worker(self, device_index: Optional[int]) -> None:
        try:
            import sounddevice as sd  # type: ignore
            import numpy as np        # type: ignore

            def audio_callback(indata, frames, time_info, status):
                if status and self.on_error:
                    self.on_error(f"Audio buffer status: {status}")

                # Compute RMS audio volume level
                try:
                    rms = np.sqrt(np.mean(indata**2))
                    # Normalize roughly 0.0 to 1.0 (clamped)
                    norm_level = min(1.0, float(rms * 10.0))
                    if self.on_level:
                        self.on_level(norm_level)

                    # Send raw PCM bytes to speech chunk handler
                    if self.on_speech_chunk and norm_level > 0.03:
                        # 16-bit PCM conversion
                        pcm16 = (indata * 32767).astype(np.int16).tobytes()
                        self.on_speech_chunk(pcm16)
                except Exception as exc:
                    logger.debug(f"Audio callback processing error: {exc}")

            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_index,
                blocksize=self.chunk_size,
                dtype="float32",
                callback=audio_callback,
            )

            with self._stream:
                logger.info(f"Microphone recording started on device index: {device_index}")
                while not self._stop_event.is_set():
                    time.sleep(0.05)

        except Exception as exc:
            self.is_recording = False
            err_msg = f"Microphone error: {exc}"
            logger.error(err_msg, exc_info=True)
            if self.on_error:
                self.on_error(err_msg)
        finally:
            self.is_recording = False
            logger.info("Microphone worker terminated cleanly.")
