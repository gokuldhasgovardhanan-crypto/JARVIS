import threading
import speech_recognition as sr
import pyttsx3

from .config import WAKE_PHRASE


class VoiceEngine:
    """
    Windows starter voice engine.
    Speech recognition uses Google's online recognition endpoint.
    Speech output uses the local Windows SAPI voice via pyttsx3.
    """

    def __init__(self, on_status, on_command, on_error):
        self.on_status = on_status
        self.on_command = on_command
        self.on_error = on_error
        self.recognizer = sr.Recognizer()
        self.stop_event = threading.Event()
        self.thread = None
        self.tts_lock = threading.Lock()

    def speak(self, text: str):
        def run():
            try:
                with self.tts_lock:
                    engine = pyttsx3.init()
                    engine.setProperty("rate", 178)
                    engine.say(text)
                    engine.runAndWait()
                    engine.stop()
            except Exception as exc:
                self.on_error(f"Text-to-speech error: {exc}")
        threading.Thread(target=run, daemon=True).start()

    def start_wake_listener(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._wake_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.on_status("Voice listener stopped")

    def _recognize(self, audio):
        return self.recognizer.recognize_google(audio).lower().strip()

    def _wake_loop(self):
        self.on_status(f"Listening for '{WAKE_PHRASE}'…")
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                while not self.stop_event.is_set():
                    try:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    except sr.WaitTimeoutError:
                        continue
                    try:
                        heard = self._recognize(audio)
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as exc:
                        self.on_error(f"Speech recognition service unavailable: {exc}")
                        self.on_status("Voice listener paused")
                        return

                    if WAKE_PHRASE in heard:
                        self.on_status("Wake word detected — listening for command…")
                        self.speak("Yes?")
                        try:
                            command_audio = self.recognizer.listen(
                                source, timeout=5, phrase_time_limit=10
                            )
                            command = self._recognize(command_audio)
                            self.on_command(command)
                        except sr.WaitTimeoutError:
                            self.on_status("No command heard. Listening again…")
                        except sr.UnknownValueError:
                            self.on_status("I couldn't understand that. Listening again…")
                        except sr.RequestError as exc:
                            self.on_error(f"Speech recognition service unavailable: {exc}")
                            return
                        self.on_status(f"Listening for '{WAKE_PHRASE}'…")
        except Exception as exc:
            self.on_error(
                "Could not start microphone listening. Check Windows microphone permission "
                f"and that PyAudio is installed. Details: {exc}"
            )
