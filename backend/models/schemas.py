from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str
    language: Optional[str] = "en"
    timestamp: Optional[str] = None

class RAGSource(BaseModel):
    id: str
    category: str
    title: str
    snippet: str
    relevance_score: float
    source_type: Optional[str] = "knowledge_base" # "uploaded_document" or "knowledge_base"
    document_name: Optional[str] = None
    page: Optional[int] = None
    chunk_id: Optional[str] = None
    section_heading: Optional[str] = None
    tfidf_score: Optional[float] = None
    keyword_score: Optional[float] = None
    semantic_score: Optional[float] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default-session"
    language: Optional[str] = "auto" # "auto" or specific code
    model_preference: Optional[str] = "api" # "api" or "local_small"
    input_type: Optional[str] = "text" # "text" or "voice"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    detected_language: str
    language_name: str
    language_flag: str
    sources: List[RAGSource]
    model_used: str
    latency_ms: float
    input_type: str
    audio_base64: Optional[str] = None
    disclaimer: str
    active_document: Optional[str] = None

class STTResponse(BaseModel):
    success: bool
    text: str
    detected_language: str
    language_name: str
    language_flag: str
    latency_ms: float
    confidence: Optional[float] = 1.0
    error: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = "en"

class TTSResponse(BaseModel):
    success: bool
    audio_base64: Optional[str] = None
    audio_format: str = "audio/mp3"
    language: str
    latency_ms: float
    error: Optional[str] = None

class LanguageDetectRequest(BaseModel):
    text: str

class LanguageDetectResponse(BaseModel):
    text: str
    detected_language: str
    language_name: str
    language_flag: str
    confidence: float

class RetrieveRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3
    session_id: Optional[str] = None

class RetrieveResponse(BaseModel):
    query: str
    detected_language: str
    results: List[RAGSource]
    active_document: Optional[str] = None

class DocumentUploadResponse(BaseModel):
    success: bool
    session_id: str
    document_name: str
    file_type: str
    total_pages: int
    total_chunks: int
    message: str
    error: Optional[str] = None

class DocumentCurrentResponse(BaseModel):
    active: bool
    session_id: str
    document_name: Optional[str] = None
    file_type: Optional[str] = None
    total_pages: Optional[int] = None
    total_chunks: Optional[int] = None
    uploaded_at: Optional[float] = None

class DocumentDeleteResponse(BaseModel):
    success: bool
    session_id: str
    message: str

class BenchmarkMetric(BaseModel):
    model_name: str
    model_type: str # "API Cloud Model" or "Small Local Model (3B)"
    model_size: str
    ram_usage: str
    avg_latency_ms: float
    tamil_quality: str
    hindi_quality: str
    english_quality: str
    telugu_quality: str
    kannada_quality: str
    malayalam_quality: str
    rag_accuracy: str
    efficiency_rating: str
    hardware_tested: str
    notes: str

class BenchmarkReport(BaseModel):
    timestamp: str
    evaluation_criteria: List[str]
    models: List[BenchmarkMetric]
    summary_verdict: str
