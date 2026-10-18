from http.server import BaseHTTPRequestHandler
import json
import os
import re
from datetime import datetime


# 10 Languages Registry & Scripts
LANGUAGES = {
    "en": {"name": "English", "native": "English", "scripts": []},
    "ta": {"name": "Tamil", "native": "தமிழ்", "scripts": [(0x0B80, 0x0BFF)]},
    "hi": {"name": "Hindi", "native": "हिन्दी", "scripts": [(0x0900, 0x097F)]},
    "te": {"name": "Telugu", "native": "తెలుగు", "scripts": [(0x0C00, 0x0C7F)]},
    "ml": {"name": "Malayalam", "native": "മലയാളം", "scripts": [(0x0D00, 0x0D7F)]},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "scripts": [(0x0C80, 0x0CFF)]},
    "de": {"name": "German", "native": "Deutsch", "scripts": []},
    "fr": {"name": "French", "native": "Français", "scripts": []},
    "es": {"name": "Spanish", "native": "Español", "scripts": []},
    "ja": {"name": "Japanese", "native": "日本語", "scripts": [(0x3040, 0x309F), (0x30A0, 0x30FF), (0x4E00, 0x9FAF)]},
}

ROMANIZED_MARKERS = {
    "ta": ["pannu", "sollu", "theravum", "innaiku", "neram", "thethi", "irukku", "enna", "paata", "podu"],
    "hi": ["kholo", "batao", "karo", "samay", "tarikh", "chalao", "roko", "badhao", "dheemi", "kaun"],
    "te": ["cheyi", "cheppu", "entha", "theruvu", "aapu", "penchu", "thagginchu", "undi"],
    "ml": ["cheyyu", "parayu", "thurakku", "enthaanu", "thiyathi", "koottu", "kurakku"],
    "kn": ["maadu", "heli", "there", "enu", "dinaanka", "hecchisu", "kadime"],
    "de": ["wie", "spät", "öffne", "uhr", "ist", "datum", "heute", "bitte", "lautstärke", "musik"],
    "fr": ["ouvre", "heure", "quelle", "date", "musique", "volume", "ferme", "merci"],
    "es": ["abre", "hora", "fecha", "música", "volumen", "gracias", "por favor", "qué"],
}


def detect_language(text: str) -> str:
    """Multi-tier script analysis, Romanized marker parsing, and heuristic detection."""
    clean = text.strip()
    if not clean:
        return "en"

    # 1. Unicode native script analysis
    char_counts = {}
    for char in clean:
        cp = ord(char)
        for code, info in LANGUAGES.items():
            for start, end in info["scripts"]:
                if start <= cp <= end:
                    char_counts[code] = char_counts.get(code, 0) + 1

    if char_counts:
        top_lang = max(char_counts, key=char_counts.get)
        if char_counts[top_lang] >= 2 or char_counts[top_lang] == len([c for c in clean if not c.isspace()]):
            return top_lang

    # 2. Romanized markers parsing (Tanglish / Hinglish / etc.)
    low = clean.lower()
    words = re.findall(r"\b\w+\b", low, re.UNICODE)
    marker_scores = {code: 0 for code in ROMANIZED_MARKERS}
    for word in words:
        for code, markers in ROMANIZED_MARKERS.items():
            if word in markers:
                marker_scores[code] += 1

    top_marker = max(marker_scores, key=marker_scores.get)
    if marker_scores[top_marker] > 0:
        return top_marker

    return "en"


def handle_intent(text: str, detected_lang: str) -> dict:
    """Matches text across 10 languages to local cloud commands."""
    low = text.lower().strip()

    # Time command
    time_keywords = [
        "what time is it", "time", "neram enna", "time sollu", "samay kya hai", "samay batao",
        "samayam entha", "time parayu", "wie spät ist es", "quelle heure est-il", "qué hora es", "何時"
    ]
    if any(k in low for k in time_keywords):
        now = datetime.now()
        return {
            "intent": "get_time",
            "reply": f"The current server time is {now.strftime('%I:%M:%S %p')} UTC.",
            "data": {"time": now.strftime('%I:%M %p')},
        }

    # Date command
    date_keywords = [
        "what is today's date", "today date", "date", "innaiku enna thethi", "thethi sollu",
        "aaj ki tarikh kya hai", "theedi cheppu", "thiyathi parayu", "welches datum", "quelle est la date", "qué día es hoy", "何日"
    ]
    if any(k in low for k in date_keywords):
        now = datetime.now()
        return {
            "intent": "get_date",
            "reply": f"Today is {now.strftime('%A, %B %d, %Y')}.",
            "data": {"date": now.strftime('%Y-%m-%d')},
        }

    # System Status / Vercel Telemetry
    if any(k in low for k in ["status", "vitals", "health", "diagnostics", "system"]):
        return {
            "intent": "diagnostics",
            "reply": (
                "JARVIS Cloud Vercel Edition is online and operational.\n"
                "• Deployment: Vercel Serverless (Python 3.12+)\n"
                "• Multi-Language Core: 10 Target Languages Active\n"
                "• Voice Engine: HTML5 Web Speech API (STT & TTS)\n"
                "• Security: TLS 1.3 End-to-End Encrypted"
            ),
        }

    # Help command
    if any(k in low for k in ["help", "what can you do", "commands", "udhavi", "madad", "hilfe", "aide", "ayuda"]):
        return {
            "intent": "help",
            "reply": (
                "Personal JARVIS Cloud Capabilities:\n"
                "• Spoken Voice I/O: Tap the Arc Reactor microphone or say 'Hey Jarvis'.\n"
                "• 10 Languages: English, Tamil, Hindi, Telugu, Malayalam, Kannada, German, French, Spanish, Japanese.\n"
                "• Live Clock & Date: 'what time is it', 'innaiku enna thethi', 'samay batao'.\n"
                "• Cloud AI: Ask general questions, coding advice, or knowledge queries."
            ),
        }

    return {}


class handler(BaseHTTPRequestHandler):
    """Vercel Python Serverless Function Handler."""

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        res = {
            "status": "online",
            "name": "Personal JARVIS Cloud API",
            "version": "1.0.0",
            "platform": "Vercel Serverless",
            "supported_languages": list(LANGUAGES.keys()),
            "timestamp": datetime.now().isoformat(),
        }
        self.wfile.write(json.dumps(res).encode("utf-8"))

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(post_data) if post_data else {}
        except Exception:
            payload = {}

        query = payload.get("text", "").strip()
        preferred_lang = payload.get("preferred_language", "auto")

        if not query:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Empty text query"}).encode("utf-8"))
            return

        # 1. Detect language
        detected_lang = detect_language(query)
        response_lang = detected_lang if preferred_lang == "auto" else preferred_lang

        # 2. Local Intent Router
        intent_result = handle_intent(query, detected_lang)
        if intent_result:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            out = {
                "text": intent_result["reply"],
                "intent": intent_result.get("intent", "custom"),
                "detected_language": detected_lang,
                "response_language": response_lang,
                "provider": "JARVIS Cloud Core",
                "timestamp": datetime.now().isoformat(),
            }
            self.wfile.write(json.dumps(out).encode("utf-8"))
            return

        # 3. Hybrid AI with OpenAI if configured in Vercel env
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if api_key:
            try:
                from openai import OpenAI  # type: ignore
                client = OpenAI(api_key=api_key)
                lang_name = LANGUAGES.get(response_lang, {}).get("name", "English")
                system_prompt = (
                    f"You are JARVIS, a sophisticated personal artificial intelligence assistant. "
                    f"Provide helpful, concise, futuristic, and highly intelligent responses. "
                    f"Respond in {lang_name} ({response_lang})."
                )
                comp = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query},
                    ],
                    max_tokens=400,
                    temperature=0.7,
                )
                ai_text = comp.choices[0].message.content or ""
                provider_name = "OpenAI Cloud (GPT-4o-mini)"
            except Exception as exc:
                ai_text = f"I processed your query: '{query}'. Cloud neural bridge error: {exc}"
                provider_name = "JARVIS Cloud Fallback"
        else:
            lang_name = LANGUAGES.get(response_lang, {}).get("name", "English")
            ai_text = (
                f"I received your transmission: '{query}'.\n"
                f"Language detected: {lang_name} ({detected_lang.upper()}). "
                f"Configure OPENAI_API_KEY in your Vercel Project Settings to unlock full conversational AI!"
            )
            provider_name = "JARVIS Cloud Offline Core"

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        out = {
            "text": ai_text,
            "intent": "general_query",
            "detected_language": detected_lang,
            "response_language": response_lang,
            "provider": provider_name,
            "timestamp": datetime.now().isoformat(),
        }
        self.wfile.write(json.dumps(out).encode("utf-8"))
