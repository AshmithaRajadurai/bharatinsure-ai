"""
Document Management API for BharatInsure AI.
Endpoints for uploading, inspecting, and removing session-based insurance documents.
"""

from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException
from typing import Optional
from backend.models.schemas import (
    DocumentUploadResponse,
    DocumentCurrentResponse,
    DocumentDeleteResponse
)
from backend.services.rag.document_processor import DocumentProcessor
from backend.services.rag.document_retriever import document_retriever

router = APIRouter()

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024 # 15 MB limit

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document_endpoint(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form("default-session")
):
    """
    Upload an insurance policy or document (PDF, DOCX, TXT).
    Extracts text, splits into page-preserving chunks, builds lightweight TF-IDF index,
    and associates it with the current user session for RAG querying.
    """
    sid = session_id or "default-session"
    filename = file.filename or "uploaded_document.pdf"
    lower_name = filename.lower()

    if not (lower_name.endswith(".pdf") or lower_name.endswith(".docx") or lower_name.endswith(".txt")):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{filename}'. Supported formats are: PDF (.pdf), Word (.docx), and Text (.txt)."
        )

    try:
        content = await file.read()
        if not content or len(content) == 0:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")

        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail="File size exceeds maximum limit of 15MB. Please upload a smaller document."
            )

        # Process, extract text, chunk, and build TF-IDF index
        indexed_data = DocumentProcessor.process_and_index_document(content, filename)

        # Store in session document store
        document_retriever.add_document(sid, indexed_data)

        return DocumentUploadResponse(
            success=True,
            session_id=sid,
            document_name=filename,
            file_type=indexed_data["file_type"],
            total_pages=indexed_data["total_pages"],
            total_chunks=indexed_data["total_chunks"],
            message=f"Successfully extracted {indexed_data['total_chunks']} chunks across {indexed_data['total_pages']} pages. Document ready for questions."
        )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@router.get("/documents/current", response_model=DocumentCurrentResponse)
async def get_current_document_endpoint(session_id: Optional[str] = Query("default-session")):
    """
    Check if a document is currently active for the user session.
    """
    sid = session_id or "default-session"
    info = document_retriever.get_document_info(sid)
    if not info:
        return DocumentCurrentResponse(active=False, session_id=sid)

    return DocumentCurrentResponse(
        active=True,
        session_id=sid,
        document_name=info["document_name"],
        file_type=info["file_type"],
        total_pages=info["total_pages"],
        total_chunks=info["total_chunks"],
        uploaded_at=info.get("uploaded_at")
    )

@router.delete("/documents/current", response_model=DocumentDeleteResponse)
async def delete_current_document_endpoint(session_id: Optional[str] = Query("default-session")):
    """
    Remove the uploaded document from the current session.
    Stops retrieving from the document and reverts session to Base Knowledge Base only.
    """
    sid = session_id or "default-session"
    removed = document_retriever.remove_document(sid)
    msg = "Active document removed from session. Reverted to Base Insurance Knowledge Base." if removed else "No active document was found for this session."

    return DocumentDeleteResponse(
        success=True,
        session_id=sid,
        message=msg
    )
