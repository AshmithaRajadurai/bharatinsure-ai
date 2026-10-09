"""
Language Management and Detection API endpoints.
"""

from fastapi import APIRouter
from typing import Dict, Any, List
from backend.models.schemas import LanguageDetectRequest, LanguageDetectResponse
from backend.services.language.detector import LanguageDetector, SUPPORTED_LANGUAGES

router = APIRouter()

@router.get("/languages")
async def get_supported_languages():
    """Returns the list of all supported Indian languages with localization details."""
    lang_list = []
    for code, details in SUPPORTED_LANGUAGES.items():
        lang_list.append({
            "code": code,
            "name": details["name"],
            "native": details["native"],
            "flag": details["flag"],
            "stt_code": details["stt_code"],
            "tts_code": details["tts_code"]
        })
    return {"languages": lang_list}

@router.post("/detect-language", response_model=LanguageDetectResponse)
async def detect_language_endpoint(request: LanguageDetectRequest):
    """Detect language of arbitrary input text."""
    detected_lang, confidence = LanguageDetector.detect(request.text)
    lang_info = LanguageDetector.get_language_info(detected_lang)

    return LanguageDetectResponse(
        text=request.text,
        detected_language=detected_lang,
        language_name=lang_info["name"],
        language_flag=lang_info["flag"],
        confidence=confidence
    )
