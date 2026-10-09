"""
Speech APIs for BharatInsure AI: Speech-to-Text & Text-to-Speech.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from backend.models.schemas import STTResponse, TTSRequest, TTSResponse
from backend.services.speech.stt_service import stt_service
from backend.services.speech.tts_service import tts_service

router = APIRouter()

@router.post("/speech-to-text", response_model=STTResponse)
async def speech_to_text_endpoint(
    audio_file: UploadFile = File(...),
    hint_language: Optional[str] = Form("auto")
):
    """
    Accept an uploaded audio recording and convert to text with language detection.
    """
    try:
        content = await audio_file.read()
        if not content or len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty audio recording received.")

        result = stt_service.transcribe_audio_file(
            file_bytes=content,
            filename=audio_file.filename or "recording.wav",
            hint_language=hint_language or "auto"
        )

        return STTResponse(
            success=result["success"],
            text=result["text"],
            detected_language=result["detected_language"],
            language_name=result["language_name"],
            language_flag=result["language_flag"],
            latency_ms=result["latency_ms"],
            confidence=result["confidence"],
            error=result["error"]
        )
    except Exception as e:
        return STTResponse(
            success=False,
            text="",
            detected_language="en",
            language_name="English",
            language_flag="🇮🇳",
            latency_ms=0.0,
            confidence=0.0,
            error=f"STT processing failed: {str(e)}"
        )

@router.post("/text-to-speech", response_model=TTSResponse)
async def text_to_speech_endpoint(request: TTSRequest):
    """
    Convert text to speech audio using the detected response language.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    res = tts_service.synthesize_speech(
        text=request.text,
        lang_code=request.language or "en"
    )

    return TTSResponse(
        success=res["success"],
        audio_base64=res["audio_base64"],
        audio_format=res["audio_format"],
        language=res["language"],
        latency_ms=res["latency_ms"],
        error=res["error"]
    )
