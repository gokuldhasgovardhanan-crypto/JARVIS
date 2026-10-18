from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class LanguageSpec:
    code: str                  # ISO 639-1 code (e.g., "ta", "en")
    display_name: str          # English display name (e.g., "Tamil")
    native_name: str           # Native script display name (e.g., "தமிழ்")
    locale: str                # Standard locale tag (e.g., "ta-IN")
    supports_local_stt: bool = True   # Faster-Whisper multilingual support
    supports_cloud_stt: bool = True
    local_stt_model_tier: str = "base"  # Recommended model tier
    supports_local_tts: bool = False   # Set dynamically by TTS engine detection
    supports_cloud_tts: bool = True
    cloud_voice_name: str = "alloy"
    script_ranges: List[Tuple[int, int]] = field(default_factory=list)
    romanized_markers: List[str] = field(default_factory=list)


class LanguageRegistry:
    """Centralized registry for the 10 supported JARVIS languages."""

    def __init__(self):
        self._languages: Dict[str, LanguageSpec] = {}
        self._init_languages()

    def _init_languages(self) -> None:
        specs = [
            LanguageSpec(
                code="en",
                display_name="English",
                native_name="English",
                locale="en-US",
                supports_local_stt=True,
                supports_local_tts=True,
                cloud_voice_name="alloy",
                script_ranges=[],
                romanized_markers=["the", "is", "please", "open", "what", "time", "date"],
            ),

            LanguageSpec(
                code="ta",
                display_name="Tamil",
                native_name="தமிழ்",
                locale="ta-IN",
                supports_local_stt=True,
                supports_local_tts=False,  # Detected at runtime
                cloud_voice_name="nova",
                script_ranges=[(0x0B80, 0x0BFF)],
                romanized_markers=[
                    "pannu", "sollu", "theravum", "innaiku", "neram", "thethi",
                    "idhai", "enna", "vendaam", "aam", "vanakkam", "eppadi",
                    "nandri", "mudiyum", "kaattu"
                ],
            ),
            LanguageSpec(
                code="hi",
                display_name="Hindi",
                native_name="हिन्दी",
                locale="hi-IN",
                supports_local_stt=True,
                supports_local_tts=False,
                cloud_voice_name="shimmer",
                script_ranges=[(0x0900, 0x097F)],
                romanized_markers=[
                    "kholo", "batao", "karo", "samay", "tarikh", "aaj", "kya",
                    "madad", "namaste", "shukriya", "dikhao", "mita", "rakho"
                ],
            ),
            LanguageSpec(
                code="te",
                display_name="Telugu",
                native_name="తెలుగు",
                locale="te-IN",
                supports_local_stt=True,
                supports_local_tts=False,
                cloud_voice_name="nova",
                script_ranges=[(0x0C00, 0x0C7F)],
                romanized_markers=[
                    "chey", "cheppu", "teruvu", "e roju", "samayam", "namaskaram"
                ],
            ),
            LanguageSpec(
                code="ml",
                display_name="Malayalam",
                native_name="മലയാളം",
                locale="ml-IN",
                supports_local_stt=True,
                supports_local_tts=False,
                cloud_voice_name="nova",
                script_ranges=[(0x0D00, 0x0D7F)],
                romanized_markers=[
                    "parayu", "thura", "samayam", "namaskaram", "nanni"
                ],
            ),
            LanguageSpec(
                code="kn",
                display_name="Kannada",
                native_name="ಕನ್ನಡ",
                locale="kn-IN",
                supports_local_stt=True,
                supports_local_tts=False,
                cloud_voice_name="nova",
                script_ranges=[(0x0C80, 0x0CFF)],
                romanized_markers=[
                    "madi", "heli", "tereyi", "samaya", "namaskara"
                ],
            ),
            LanguageSpec(
                code="de",
                display_name="German",
                native_name="Deutsch",
                locale="de-DE",
                supports_local_stt=True,
                supports_local_tts=True,
                cloud_voice_name="onyx",
                script_ranges=[],
                romanized_markers=[
                    "öffne", "wie", "spät", "uhr", "heute", "datum", "bitte",
                    "danke", "hilfe", "lösche", "notiz", "merk", "ist"
                ],
            ),
            LanguageSpec(
                code="fr",
                display_name="French",
                native_name="Français",
                locale="fr-FR",
                supports_local_stt=True,
                supports_local_tts=True,
                cloud_voice_name="fable",
                script_ranges=[],
                romanized_markers=[
                    "ouvre", "quelle", "heure", "aujourd'hui", "date", "merci",
                    "aide", "efface", "notes", "bonjour", "s'il"
                ],
            ),
            LanguageSpec(
                code="es",
                display_name="Spanish",
                native_name="Español",
                locale="es-ES",
                supports_local_stt=True,
                supports_local_tts=True,
                cloud_voice_name="echo",
                script_ranges=[],
                romanized_markers=[
                    "abre", "qué", "hora", "hoy", "fecha", "gracias", "ayuda",
                    "borra", "notas", "hola", "por"
                ],
            ),
            LanguageSpec(
                code="ja",
                display_name="Japanese",
                native_name="日本語",
                locale="ja-JP",
                supports_local_stt=True,
                supports_local_tts=True,
                cloud_voice_name="alloy",
                script_ranges=[
                    (0x3040, 0x309F),  # Hiragana
                    (0x30A0, 0x30FF),  # Katakana
                    (0x4E00, 0x9FFF),  # Kanji
                ],
                romanized_markers=[
                    "arigatou", "konnichiwa", "jikan", "kyou", "tasukete"
                ],
            ),
        ]

        for spec in specs:
            self._languages[spec.code] = spec

    def get(self, code: str) -> Optional[LanguageSpec]:
        """Gets language specification by ISO code (case-insensitive)."""
        return self._languages.get(code.lower().strip())

    def get_by_name(self, name: str) -> Optional[LanguageSpec]:
        """Looks up language by display or native name."""
        low = name.lower().strip()
        for spec in self._languages.values():
            if spec.display_name.lower() == low or spec.native_name.lower() == low:
                return spec
        return None

    def all_languages(self) -> List[LanguageSpec]:
        """Returns all 10 registered languages."""
        return list(self._languages.values())

    def supported_codes(self) -> List[str]:
        """Returns list of the 10 supported ISO codes."""
        return list(self._languages.keys())

    def resolve_language(self, identifier: str, fallback: str = "en") -> str:
        """Normalizes any language name or code to a supported 2-letter code."""
        clean = identifier.lower().strip()
        if clean in self._languages:
            return clean
        match = self.get_by_name(clean)
        return match.code if match else fallback


language_registry = LanguageRegistry()
