"""
BharatInsure AI – Multilingual Fintech & Insurance Assistant
FastAPI Backend Main Application
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import API routes
from backend.api.chat import router as chat_router
from backend.api.speech import router as speech_router
from backend.api.languages import router as languages_router
from backend.api.retrieve import router as retrieve_router
from backend.api.benchmark import router as benchmark_router
from backend.api.documents import router as documents_router

from contextlib import asynccontextmanager
import threading
from backend.services.llm.local_model_service import local_llm_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Asynchronously warm up Ollama model in RAM so user turns never experience cold start
    def warm_up():
        print("[Startup] Warming up Ollama local model in RAM...", flush=True)
        local_llm_service.preload_model(keep_alive="60m")
        print("[Startup] Ollama local model successfully resident in RAM.", flush=True)
    threading.Thread(target=warm_up, daemon=True).start()
    yield

app = FastAPI(
    title="BharatInsure AI – Multilingual Fintech & Insurance Assistant",
    description="Multilingual Insurance Assistant with RAG, Speech-to-Text, Voice synthesis, and Model Efficiency Benchmarks",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(chat_router, tags=["Chat"])
app.include_router(documents_router, tags=["Documents"])
app.include_router(speech_router, tags=["Speech"])
app.include_router(languages_router, tags=["Languages"])
app.include_router(retrieve_router, tags=["RAG Retrieval"])
app.include_router(benchmark_router, tags=["Benchmarks"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "BharatInsure AI Backend",
        "version": "1.0.0",
        "supported_languages": ["en", "hi", "ta", "te", "kn", "ml", "mr", "bn", "gu"],
        "rag_status": "active",
        "speech_status": "active",
        "models_available": ["Cloud API Baseline", "Local Small Model (Qwen2.5-3B)"]
    }

@app.get("/")
async def root():
    return JSONResponse(
        content={
            "app": "BharatInsure AI – Multilingual Fintech & Insurance Assistant",
            "message": "Welcome to BharatInsure AI API server. Access /docs for interactive OpenAPI documentation.",
            "health": "/health",
            "benchmark": "/benchmark"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
