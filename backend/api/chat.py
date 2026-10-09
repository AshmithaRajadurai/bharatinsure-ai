"""
Chat Endpoint for BharatInsure AI.
Orchestrates: Input -> Language Detection -> Memory -> Multi-Source RAG (Doc + KB) -> LLM -> Response.
"""

from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.language.detector import LanguageDetector
from backend.services.memory.session_memory import session_memory
from backend.services.rag.retriever import rag_retriever
from backend.services.rag.document_retriever import document_retriever
from backend.services.llm.llm_manager import llm_manager, DISCLAIMER_TEXT

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # 1. Automatic Language Detection
    if request.language and request.language != "auto":
        detected_lang = request.language
    else:
        detected_lang, _ = LanguageDetector.detect(request.message)

    lang_info = LanguageDetector.get_language_info(detected_lang)

    # 2. Retrieve Conversation Memory & History (compact to preserve speed)
    session_id = request.session_id or "default-session"
    history_text = session_memory.format_history_for_prompt(session_id, limit=2)

    # 3. Check for Active Uploaded Document in Session
    active_doc_info = document_retriever.get_document_info(session_id)
    active_doc_name = active_doc_info["document_name"] if active_doc_info else None

    # 4. Multi-Source Insurance RAG Retrieval (Uploaded Document + Base Knowledge Base)
    sources = rag_retriever.retrieve_multi_source(
        query=request.message,
        session_id=session_id,
        top_k=3
    )

    # Inferred topic category for memory tagging
    top_category = sources[0].category if sources else "General Insurance"

    # 5. Multilingual LLM Generation with Active Document Grounding
    llm_result = llm_manager.generate_response(
        query=request.message,
        detected_language=detected_lang,
        sources=sources,
        conversation_history_text=history_text,
        model_preference=request.model_preference or "api",
        active_document=active_doc_name
    )

    # 6. Save Turn to Conversational Memory (maintaining cross-lingual dialogue)
    session_memory.add_turn(
        session_id=session_id,
        user_content=request.message,
        assistant_content=llm_result["response"],
        user_lang=detected_lang,
        category=top_category
    )

    return ChatResponse(
        response=llm_result["response"],
        session_id=session_id,
        detected_language=detected_lang,
        language_name=lang_info["name"],
        language_flag=lang_info["flag"],
        sources=sources,
        model_used=llm_result["model_used"],
        latency_ms=llm_result["latency_ms"],
        input_type=request.input_type or "text",
        audio_base64=None,
        disclaimer=DISCLAIMER_TEXT,
        active_document=active_doc_name
    )
