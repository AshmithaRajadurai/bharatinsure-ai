"""
Multilingual Speech-to-Text (STT) Service for BharatInsure AI.
Processes audio uploads and transcribes them in Indian languages.
"""

import os
import io
import time
import speech_recognition as sr
from typing import Dict, Any, Tuple
from backend.services.language.detector import LanguageDetector

class STTService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 250
        self.recognizer.dynamic_energy_threshold = True

    def transcribe_audio_file(self, file_bytes: bytes, filename: str, hint_language: str = "auto") -> Dict[str, Any]:
        """
        Transcribe an uploaded audio file into text.
        Returns: { "success": bool, "text": str, "detected_language": str, "confidence": float, "latency_ms": float, "error": str }
        """
        start_time = time.time()
        
        try:
            is_wav = filename.lower().endswith(".wav")
            
            # If not wav, attempt conversion using pydub if ffmpeg is available
            if not is_wav:
                try:
                    from pydub import AudioSegment
                    audio_segment = AudioSegment.from_file(io.BytesIO(file_bytes))
                    wav_io = io.BytesIO()
                    audio_segment.export(wav_io, format="wav")
                    wav_io.seek(0)
                    audio_source = wav_io
                except Exception as conv_err:
                    print(f"[STT] Audio conversion fallback: {conv_err}")
                    audio_source = io.BytesIO(file_bytes)
            else:
                audio_source = io.BytesIO(file_bytes)

            with sr.AudioFile(audio_source) as source:
                # Brief ambient noise calibration
                try:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                except Exception:
                    pass
                audio_data = self.recognizer.record(source)

            # Determine primary language code for recognizer
            lang_code = hint_language if hint_language != "auto" else "en"
            stt_locale = LanguageDetector.get_language_info(lang_code)["stt_code"]

            # Recognize using Google Speech Recognition API with multi-dialect fallback
            text = None
            try:
                text = self.recognizer.recognize_google(audio_data, language=stt_locale)
            except sr.UnknownValueError:
                # If recognition failed in selected regional language, attempt en-IN (Indian English / code-mixed)
                if stt_locale != "en-IN":
                    try:
                        text = self.recognizer.recognize_google(audio_data, language="en-IN")
                    except Exception:
                        pass
                # Or try hi-IN fallback
                if not text and stt_locale != "hi-IN":
                    try:
                        text = self.recognizer.recognize_google(audio_data, language="hi-IN")
                    except Exception:
                        pass
                if not text:
                    raise sr.UnknownValueError()

            text = text.strip()
            
            # Detect language of transcribed text
            detected_lang, confidence = LanguageDetector.detect(text)
            lang_info = LanguageDetector.get_language_info(detected_lang)

            latency_ms = round((time.time() - start_time) * 1000, 1)

            return {
                "success": True,
                "text": text,
                "detected_language": detected_lang,
                "language_name": lang_info["name"],
                "language_flag": lang_info["flag"],
                "confidence": confidence,
                "latency_ms": latency_ms,
                "error": None
            }

        except sr.UnknownValueError:
            latency_ms = round((time.time() - start_time) * 1000, 1)
            return {
                "success": False,
                "text": "",
                "detected_language": "en",
                "language_name": "English",
                "language_flag": "🇮🇳",
                "confidence": 0.0,
                "latency_ms": latency_ms,
                "error": "Could not understand the audio. Please speak clearly into the microphone."
            }
        except sr.RequestError as req_err:
            latency_ms = round((time.time() - start_time) * 1000, 1)
            return {
                "success": False,
                "text": "",
                "detected_language": "en",
                "language_name": "English",
                "language_flag": "🇮🇳",
                "confidence": 0.0,
                "latency_ms": latency_ms,
                "error": f"Speech recognition service unreachable: {str(req_err)}"
            }
        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 1)
            return {
                "success": False,
                "text": "",
                "detected_language": "en",
                "language_name": "English",
                "language_flag": "🇮🇳",
                "confidence": 0.0,
                "latency_ms": latency_ms,
                "error": f"Speech processing error: {str(e)}"
            }

# Singleton instance
stt_service = STTService()
