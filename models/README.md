# JARVIS Local Speech and AI Models Directory

This directory stores downloaded local voice, wake-word, and speech recognition models. Large models are never bundled into the repository or downloaded silently.

## 1. Speech Recognition (Faster-Whisper)

JARVIS supports multilingual offline speech transcription using `faster-whisper` (powered by CTranslate2 and ONNX Runtime).

| Model Size | Parameters | VRAM / RAM Required | Relative Speed | Typical Accuracy |
| :--- | :--- | :--- | :--- | :--- |
| `tiny` | 39 M | ~1 GB | Fastest (32x) | Good for basic English |
| `base` (Recommended) | 74 M | ~1.5 GB | Fast (16x) | Solid for 10 target languages |
| `small` | 244 M | ~2.5 GB | Medium (6x) | High accuracy on code-switching |
| `medium` | 769 M | ~5 GB | Slower (2x) | Near state-of-the-art multilingual |

To configure your model size, set `JARVIS_WHISPER_MODEL` in your `.env` file (e.g. `JARVIS_WHISPER_MODEL=base`).

## 2. Wake-Word Engine

JARVIS uses local activation ("Hey Jarvis").
Wake-word models run locally with sub-second latency and zero external network transmission.

## 3. Local Text-to-Speech (TTS)

- Windows native SAPI voices via `pyttsx3`
- Optional offline high-fidelity neural voices via `piper`
