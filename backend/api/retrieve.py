"""
RAG Transparency & Inspection API.
Allows developers, evaluators, and users to inspect retrieved knowledge chunks directly
from both Base Knowledge Base and Session Uploaded Documents.
"""

from fastapi import APIRouter
from backend.models.schemas import RetrieveRequest, RetrieveResponse
from backend.services.rag.retriever import rag_retriever
from backend.services.rag.document_retriever import document_retriever
from backend.services.language.detector import LanguageDetector

router = APIRouter()

@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_endpoint(request: RetrieveRequest):
    """
    Search and inspect relevant insurance documents directly from the Base Knowledge Base
    and any active session uploaded documents.
    """
    detected_lang, _ = LanguageDetector.detect(request.query)
    sid = request.session_id or "default-session"

    results = rag_retriever.retrieve_multi_source(
        query=request.query,
        session_id=sid,
        top_k=request.top_k or 3
    )

    doc_info = document_retriever.get_document_info(sid)
    active_doc_name = doc_info["document_name"] if doc_info else None

    return RetrieveResponse(
        query=request.query,
        detected_language=detected_lang,
        results=results,
        active_document=active_doc_name
    )
