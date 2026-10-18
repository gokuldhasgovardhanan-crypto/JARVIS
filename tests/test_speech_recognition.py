import pytest
from jarvis.voice.speech_recognition import (
    FasterWhisperSTTProvider,
    CloudSTTProvider,
    STTManager,
    TranscriptionResult,
    BaseSTTProvider,
)


class MockSTT(BaseSTTProvider):
    def is_available(self) -> bool:
        return True

    def get_provider_name(self) -> str:
        return "Mock STT"

    def transcribe(self, audio_data, sample_rate=16000, language=None):
        return TranscriptionResult(
            text="Hello Jarvis",
            language="en",
            probability=0.98,
            duration=1.2,
            is_local=True,
            provider_name="Mock STT",
        )


def test_faster_whisper_availability():
    provider = FasterWhisperSTTProvider(model_size="base")
    # faster_whisper was installed in .venv, so it should be available
    assert provider.is_available() is True
    assert "Faster-Whisper" in provider.get_provider_name()


def test_cloud_stt_unconfigured():
    provider = CloudSTTProvider(api_key="")
    assert provider.is_available() is False
    with pytest.raises(RuntimeError, match="not configured"):
        provider.transcribe(b"dummy")


def test_stt_manager_delegation():
    mock = MockSTT()
    manager = STTManager(local_provider=mock)
    res = manager.transcribe(b"dummy_audio_bytes")
    assert res.text == "Hello Jarvis"
    assert res.language == "en"
    assert res.probability == 0.98
