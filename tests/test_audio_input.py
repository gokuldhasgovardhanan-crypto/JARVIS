import pytest
from jarvis.voice.audio_input import AudioInputService, AudioDeviceInfo


def test_device_enumeration():
    devices = AudioInputService.get_input_devices()
    # On systems with mic, len > 0; on virtual CI/audio-less, returns empty list without error
    assert isinstance(devices, list)
    for dev in devices:
        assert isinstance(dev.name, str)
        assert dev.channels >= 1
        assert dev.default_samplerate > 0


def test_audio_input_lifecycle():
    levels = []
    audio_srv = AudioInputService(
        sample_rate=16000,
        on_level=lambda lvl: levels.append(lvl),
    )
    assert audio_srv.is_recording is False

    # Start and stop safely
    started = audio_srv.start_recording()
    assert started is True
    assert audio_srv.is_recording is True

    audio_srv.stop_recording()
    assert audio_srv.is_recording is False
