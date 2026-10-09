"""
Multilingual Text-to-Speech (TTS) Service for BharatInsure AI.
Generates audio in Tamil, Hindi, Telugu, Kannada, Malayalam, English.
"""

import io
import time
import base64
from typing import Dict, Any
from gtts import gTTS
from backend.services.language.detector import LanguageDetector

# Map to gTTS supported language codes
GTTS_LANG_MAP = {
    "en": "en",
    "hi": "hi",
    "ta": "ta",
    "te": "te",
    "kn": "kn",
    "ml": "ml",
    "mr": "mr",
    "bn": "bn",
    "gu": "gu"
}

class TTSService:
    def synthesize_speech(self, text: str, lang_code: str = "en") -> Dict[str, Any]:
        """
        Convert text into base64 MP3 audio using gTTS.
        """
        start_time = time.time()
        if not text or not text.strip():
            return {
                "success": False,
                "audio_base64": None,
                "audio_format": "audio/mp3",
                "language": lang_code,
                "latency_ms": 0.0,
                "error": "Empty text provided"
            }

        target_lang = GTTS_LANG_MAP.get(lang_code, "en")
        clean_text = text.replace("⚠️", "").replace("*", "").replace("#", "").strip()
        # Truncate to reasonable length for TTS audio
        if len(clean_text) > 400:
            clean_text = clean_text[:400] + "..."

        try:
            tts = gTTS(text=clean_text, lang=target_lang, slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_bytes = fp.read()
            b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            latency_ms = round((time.time() - start_time) * 1000, 1)

            return {
                "success": True,
                "audio_base64": b64_audio,
                "audio_format": "audio/mp3",
                "language": target_lang,
                "latency_ms": latency_ms,
                "error": None
            }
        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 1)
            return {
                "success": False,
                "audio_base64": None,
                "audio_format": "audio/mp3",
                "language": target_lang,
                "latency_ms": latency_ms,
                "error": f"TTS synthesis error: {str(e)}"
            }

# Singleton instance
tts_service = TTSService()
