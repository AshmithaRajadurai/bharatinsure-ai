"""
Multilingual Language Detection Service for BharatInsure AI.
Supports Indian languages:
- Tamil (தமிழ் - ta)
- Hindi (हिन्दी - hi)
- Telugu (తెలుగు - te)
- Kannada (ಕನ್ನಡ - kn)
- Malayalam (മലയാളം - ml)
- English (en)
- Marathi (मराठी - mr)
- Bengali (বাংলা - bn)
- Gujarati (ગુજરાતી - gu)
"""

import re
from typing import Dict, Any, Tuple

SUPPORTED_LANGUAGES = {
    "en": {
        "name": "English",
        "native": "English",
        "flag": "🇬🇧 / 🇮🇳",
        "stt_code": "en-IN",
        "tts_code": "en",
    },
    "hi": {
        "name": "Hindi",
        "native": "हिन्दी",
        "flag": "🇮🇳",
        "stt_code": "hi-IN",
        "tts_code": "hi",
    },
    "ta": {
        "name": "Tamil",
        "native": "தமிழ்",
        "flag": "🇮🇳",
        "stt_code": "ta-IN",
        "tts_code": "ta",
    },
    "te": {
        "name": "Telugu",
        "native": "తెలుగు",
        "flag": "🇮🇳",
        "stt_code": "te-IN",
        "tts_code": "te",
    },
    "kn": {
        "name": "Kannada",
        "native": "ಕನ್ನಡ",
        "flag": "🇮🇳",
        "stt_code": "kn-IN",
        "tts_code": "kn",
    },
    "ml": {
        "name": "Malayalam",
        "native": "മലയാളം",
        "flag": "🇮🇳",
        "stt_code": "ml-IN",
        "tts_code": "ml",
    },
    "mr": {
        "name": "Marathi",
        "native": "मराठी",
        "flag": "🇮🇳",
        "stt_code": "mr-IN",
        "tts_code": "mr",
    },
    "bn": {
        "name": "Bengali",
        "native": "বাংলা",
        "flag": "🇮🇳",
        "stt_code": "bn-IN",
        "tts_code": "bn",
    },
    "gu": {
        "name": "Gujarati",
        "native": "ગુજરાતી",
        "flag": "🇮🇳",
        "stt_code": "gu-IN",
        "tts_code": "gu",
    }
}

# Unicode Script Ranges
UNICODE_RANGES = [
    (r'[\u0B80-\u0BFF]', 'ta'), # Tamil
    (r'[\u0C00-\u0C7F]', 'te'), # Telugu
    (r'[\u0C80-\u0CFF]', 'kn'), # Kannada
    (r'[\u0D00-\u0D7F]', 'ml'), # Malayalam
    (r'[\u0980-\u09FF]', 'bn'), # Bengali
    (r'[\u0A80-\u0AFF]', 'gu'), # Gujarati
    (r'[\u0900-\u097F]', 'hi'), # Devanagari (Hindi / Marathi)
]

# Marathi-specific distinguishing lexical markers in Devanagari
MARATHI_MARKERS = ["आहे", "आहोत", "नाही", "काय", "कसा", "विमा", "माहिती", "करावे", "हवे", "माझे"]

# Hinglish / Tanglish / phonetic romanized Indian words fallback
HINGLISH_KEYWORDS = ["kya", "hai", "bima", "chahiye", "kaise", "kitna", "batao", "mujhe", "mera", "hoga", "policy"]
TANGLISH_KEYWORDS = ["enna", "theriyum", "venum", "eppadi", "kaappeedu", "solunga", "irukku"]
TELGLISH_KEYWORDS = ["enti", "kaavali", "ela", "undhi", "bheema", "cheppandi"]

class LanguageDetector:
    @staticmethod
    def detect(text: str) -> Tuple[str, float]:
        """
        Detect the language code and confidence score from input text.
        """
        if not text or not text.strip():
            return "en", 0.5
        
        cleaned = text.strip()

        # Count character frequencies in Indic unicode blocks
        script_counts: Dict[str, int] = {}
        for pattern, lang_code in UNICODE_RANGES:
            matches = re.findall(pattern, cleaned)
            if matches:
                script_counts[lang_code] = len(matches)

        if script_counts:
            # Pick highest count
            top_lang = max(script_counts, key=script_counts.get)
            total_indic_chars = sum(script_counts.values())
            
            # Devanagari discrimination: Hindi vs Marathi
            if top_lang == 'hi':
                words = cleaned.split()
                marathi_hits = sum(1 for w in words if any(m in w for m in MARATHI_MARKERS))
                if marathi_hits >= 2:
                    top_lang = 'mr'

            confidence = min(0.99, round(total_indic_chars / (len(cleaned.replace(" ", "")) + 1e-5), 2))
            return top_lang, max(0.85, confidence)

        # Latin script check: Hinglish/Tanglish or English
        lower_text = cleaned.lower()
        words = set(re.findall(r'\b\w+\b', lower_text))

        hinglish_hits = sum(1 for w in words if w in HINGLISH_KEYWORDS)
        tanglish_hits = sum(1 for w in words if w in TANGLISH_KEYWORDS)
        telglish_hits = sum(1 for w in words if w in TELGLISH_KEYWORDS)

        if hinglish_hits >= 2:
            return "hi", 0.88
        if tanglish_hits >= 2:
            return "ta", 0.88
        if telglish_hits >= 2:
            return "te", 0.88

        # Default to English
        return "en", 0.95

    @classmethod
    def get_language_info(cls, lang_code: str) -> Dict[str, Any]:
        """Get descriptive details for a language code."""
        info = SUPPORTED_LANGUAGES.get(lang_code, SUPPORTED_LANGUAGES["en"])
        return {
            "code": lang_code if lang_code in SUPPORTED_LANGUAGES else "en",
            "name": info["name"],
            "native": info["native"],
            "flag": info["flag"],
            "stt_code": info["stt_code"],
            "tts_code": info["tts_code"]
        }
