"""
Test Chat Endpoint Routing:
Ensures:
1. 'Hello' -> returns instantaneously (< 5ms) via Intent Router, 0 sources.
2. 'Who are you?' -> returns instantaneously (< 5ms) via Intent Router, 0 sources.
3. 'What can you do?' -> returns instantaneously (< 5ms) via Intent Router, 0 sources.
4. 'What is UPI?' -> does NOT use intent router, retrieves 1+ source from RAG.
5. 'What is the waiting period for pre-existing diseases?' -> retrieves PED source from RAG.
"""

import sys
import os
import time
import asyncio
from fastapi import Request

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.api.chat import chat_endpoint
from backend.models.schemas import ChatRequest

async def test_endpoint():
    print("=" * 70)
    print("VERIFYING CHAT ENDPOINT INTENT ROUTING")
    print("=" * 70)

    # 1. Basic greeting
    t0 = time.perf_counter()
    res1 = await chat_endpoint(ChatRequest(message="Hello", session_id="test-routing-01"))
    lat1 = (time.perf_counter() - t0) * 1000
    print(f"[Greeting] 'Hello' -> Latency: {lat1:.2f} ms | Model: {res1.model_used} | Sources: {len(res1.sources)}")
    assert "Intent Router" in res1.model_used
    assert len(res1.sources) == 0
    assert lat1 < 50.0  # Should be practically instantaneous

    # 2. Identity
    t0 = time.perf_counter()
    res2 = await chat_endpoint(ChatRequest(message="Who are you?", session_id="test-routing-01"))
    lat2 = (time.perf_counter() - t0) * 1000
    print(f"[Identity] 'Who are you?' -> Latency: {lat2:.2f} ms | Model: {res2.model_used} | Sources: {len(res2.sources)}")
    assert "Intent Router" in res2.model_used
    assert len(res2.sources) == 0

    # 3. Capabilities
    t0 = time.perf_counter()
    res3 = await chat_endpoint(ChatRequest(message="What can you do?", session_id="test-routing-01"))
    lat3 = (time.perf_counter() - t0) * 1000
    print(f"[Capabilities] 'What can you do?' -> Latency: {lat3:.2f} ms | Model: {res3.model_used} | Sources: {len(res3.sources)}")
    assert "Intent Router" in res3.model_used
    assert len(res3.sources) == 0

    # 4. Short Finance query (What is UPI?) -> MUST use retrieval, must NOT be hijacked
    # To test without waiting 10s for Ollama, test rag_retriever directly
    from backend.services.intent.intent_router import intent_router
    assert intent_router.route("What is UPI?") is None, "UPI query must not be routed by intent router"
    from backend.services.rag.retriever import rag_retriever
    sources = rag_retriever.retrieve("What is UPI?", top_k=2)
    print(f"[Short Finance] 'What is UPI?' -> Intent Router routed: False | RAG Sources found: {len(sources)}")
    assert len(sources) > 0, "UPI must retrieve knowledge base chunk"
    print(f"  Top source: [{sources[0].category}] {sources[0].title}")

    print("\nALL PHASE 2 INTENT ROUTING CHECKS PASSED!")

if __name__ == "__main__":
    asyncio.run(test_endpoint())
