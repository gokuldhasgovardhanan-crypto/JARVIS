import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from jarvis.languages.registry import language_registry, LanguageSpec
from jarvis.utils.logging_config import logger


@dataclass
class LanguageDetectionResult:
    language: str                # Normalized ISO code, e.g. "ta", "en", "de"
    confidence: float            # 0.0 to 1.0
    is_uncertain: bool           # True if confidence is below safety threshold
    method: str                  # "script_analysis", "romanized_markers", "statistical", "context", "fallback"
    details: Optional[Dict[str, Any]] = None


class LanguageDetectionService:
    """
    Robust multilingual language detector combining Unicode script analysis,
    Romanized code-switching markers, statistical text detection, and conversation context.
    """

    def __init__(self, fallback_language: str = "en"):
        self.fallback_language = fallback_language
        self._langdetect_available = False
        try:
            import langdetect  # type: ignore
            self._langdetect = langdetect
            self._langdetect_available = True
        except ImportError:
            self._langdetect = None

    def detect(
        self,
        text: str,
        speech_metadata: Optional[Dict[str, Any]] = None,
        previous_language: Optional[str] = None,
    ) -> LanguageDetectionResult:
        """
        Detects the language of an utterance, returning normalized ISO code and confidence.
        """
        cleaned = text.strip()
        if not cleaned:
            return LanguageDetectionResult(
                language=self.fallback_language,
                confidence=0.0,
                is_uncertain=True,
                method="empty_fallback",
            )

        # 1. Speech metadata prior (from Faster-Whisper if available)
        if speech_metadata and "language" in speech_metadata:
            meta_lang = speech_metadata["language"]
            meta_prob = float(speech_metadata.get("probability", 0.0))
            if meta_prob >= 0.70 and meta_lang in language_registry.supported_codes():
                logger.info(f"Language identified via STT metadata: {meta_lang} (prob={meta_prob:.2f})")
                return LanguageDetectionResult(
                    language=meta_lang,
                    confidence=meta_prob,
                    is_uncertain=False,
                    method="speech_metadata",
                )

        # 2. Unicode Native Script Analysis (High Precision)
        script_match = self._detect_by_script(cleaned)
        if script_match:
            return script_match

        # 3. Romanized Marker / Code-Switching Detection (Tanglish, Hinglish, German, etc.)
        marker_match = self._detect_by_romanized_markers(cleaned)
        if marker_match:
            return marker_match

        # 4. Statistical Text Detection (via langdetect for longer Latin text)
        if self._langdetect_available and len(cleaned.split()) >= 3 and len(cleaned) >= 12:
            try:
                # langdetect gives probabilies
                predictions = self._langdetect.detect_langs(cleaned)
                if predictions:
                    top = predictions[0]
                    detected_code = language_registry.resolve_language(top.lang, fallback="")
                    if detected_code:
                        is_uncertain = top.prob < 0.65
                        return LanguageDetectionResult(
                            language=detected_code,
                            confidence=top.prob,
                            is_uncertain=is_uncertain,
                            method="statistical",
                            details={"raw_lang": top.lang, "prob": top.prob},
                        )
            except Exception as exc:
                logger.debug(f"langdetect error: {exc}")

        # 5. Short phrase uncertainty & Conversation context check
        # Avoid switching language on single-word technical terms like "notepad", "calculator", "yes"
        words = re.findall(r"\w+", cleaned.lower())
        if len(words) <= 2:
            if previous_language and previous_language in language_registry.supported_codes():
                return LanguageDetectionResult(
                    language=previous_language,
                    confidence=0.55,
                    is_uncertain=False,
                    method="context_prior",
                )
            return LanguageDetectionResult(
                language=self.fallback_language,
                confidence=0.50,
                is_uncertain=True,
                method="short_phrase_uncertain",
            )

        # 6. Default Fallback
        return LanguageDetectionResult(
            language=self.fallback_language,
            confidence=0.40,
            is_uncertain=True,
            method="fallback",
        )

    def _detect_by_script(self, text: str) -> Optional[LanguageDetectionResult]:
        """Inspects Unicode character ranges for Indic and East Asian scripts."""
        char_counts: Dict[str, int] = {}
        total_letters = 0

        for char in text:
            if not char.isalnum():
                continue
            code_pt = ord(char)
            total_letters += 1
            for spec in language_registry.all_languages():
                for start, end in spec.script_ranges:
                    if start <= code_pt <= end:
                        char_counts[spec.code] = char_counts.get(spec.code, 0) + 1

        if total_letters == 0:
            return None

        # If any script represents >= 15% of characters
        for lang_code, count in char_counts.items():
            ratio = count / total_letters
            if ratio >= 0.15:
                confidence = min(1.0, 0.85 + (ratio * 0.15))
                return LanguageDetectionResult(
                    language=lang_code,
                    confidence=confidence,
                    is_uncertain=False,
                    method="script_analysis",
                    details={"matched_chars": count, "ratio": ratio},
                )
        return None

    def _detect_by_romanized_markers(self, text: str) -> Optional[LanguageDetectionResult]:
        """Detects Romanized mixed-language utterances via token matching."""
        tokens = set(re.findall(r"[a-zA-ZäöüÄÖÜßáéíóúÁÉÍÓÚàèìòùÀÈÌÒÙ]+", text.lower()))
        if not tokens:
            return None

        scores: Dict[str, int] = {}
        for spec in language_registry.all_languages():
            if not spec.romanized_markers or spec.code == "en":
                continue
            matched = tokens.intersection(set(spec.romanized_markers))
            if matched:
                scores[spec.code] = len(matched)

        if scores:
            best_lang = max(scores, key=scores.get)
            match_count = scores[best_lang]
            confidence = min(0.95, 0.70 + (match_count * 0.10))
            return LanguageDetectionResult(
                language=best_lang,
                confidence=confidence,
                is_uncertain=False,
                method="romanized_markers",
                details={"matched_markers": match_count},
            )
        return None
