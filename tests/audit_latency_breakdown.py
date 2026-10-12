"""
Audit & Latency Breakdown Measurement Script for BharatInsure AI.
Measures:
1. Language detection latency
2. Memory lookup/formatting latency
3. RAG retrieval latency across different query types (greeting, short finance, detailed policy)
4. Ollama model load / residency status
5. Ollama TTFT (time-to-first-token), tokens/sec, prompt eval time, eval time, total generation latency
"""

import sys
import os
import time
import json
import psutil

# Ensure UTF-8 console output on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.language.detector import LanguageDetector
from backend.services.memory.session_memory import session_memory
from backend.services.rag.retriever import rag_retriever
from backend.services.llm.local_model_service import local_llm_service
from backend.services.llm.llm_manager import llm_manager

def run_audit():
    print("=" * 70)
    print("PHASE 1: AUDIT & COMPONENT LATENCY BREAKDOWN")
    print("=" * 70)

    # 1. System Info
    vm = psutil.virtual_memory()
    print(f"System RAM: Total={vm.total / (1024**3):.2f} GB, Available={vm.available / (1024**3):.2f} GB, Used={vm.percent}%")
    cpu_count = psutil.cpu_count(logical=True)
    print(f"CPU Logical Cores: {cpu_count}")

    # 2. Ollama Status
    status = local_llm_service.get_status()
    print("\n--- Ollama Status ---")
    print(f"Model: {status['model_name']}")
    print(f"Loaded: {status['is_loaded']}")
    print(f"Quantization: {status['quantization']}")
    print(f"Model Disk Size: {status['model_disk_size_mb']} MB")
    print(f"Backend RAM: {status['backend_ram_mb']} MB, Ollama RAM: {status['ollama_ram_mb']} MB")

    # 3. Test Language Detection Latency
    print("\n--- 1. Language Detection Latency ---")
    test_phrases = [
        ("hi", "Hello how are you"),
        ("ta", "மருத்துவ காப்பீட்டில் காத்திருப்பு காலம் எவ்வளவு?"),
        ("hi_in", "स्वास्थ्य बीमा में प्रतीक्षा अवधि क्या है?"),
        ("short_fin", "What is UPI?"),
    ]
    for label, phrase in test_phrases:
        times = []
        for _ in range(5):
            t0 = time.perf_counter()
            lang, _ = LanguageDetector.detect(phrase)
            times.append((time.perf_counter() - t0) * 1000)
        avg_t = sum(times) / len(times)
        print(f"  [{label}] '{phrase[:35]}...' -> {lang} in avg {avg_t:.3f} ms")

    # 4. Test Memory Latency
    print("\n--- 2. Session Memory Latency ---")
    session_id = "audit-session-001"
    session_memory.add_turn(session_id, "Hello", "Hi there!", "en", "General")
    session_memory.add_turn(session_id, "What is health insurance?", "Health insurance covers hospital bills.", "en", "Health")
    t0 = time.perf_counter()
    hist = session_memory.format_history_for_prompt(session_id, limit=2)
    mem_lat = (time.perf_counter() - t0) * 1000
    print(f"  Memory format latency: {mem_lat:.3f} ms (History chars: {len(hist)})")

    # 5. Test RAG Retrieval Latency
    print("\n--- 3. RAG Retrieval Latency (Base KB) ---")
    rag_queries = [
        ("Greeting", "hello good morning"),
        ("Identity", "who are you and what can you do?"),
        ("Short Finance", "What is UPI?"),
        ("Waiting Period", "What is the waiting period for pre-existing diseases?"),
        ("Complex Term", "How does pure term life insurance work compared to whole life?"),
        ("Tamil Health", "மருத்துவ காப்பீட்டில் காத்திருப்பு காலம் எவ்வளவு?")
    ]
    for q_type, q_text in rag_queries:
        times = []
        res_count = 0
        top_score = 0.0
        for _ in range(3):
            t0 = time.perf_counter()
            sources = rag_retriever.retrieve(q_text, top_k=3)
            times.append((time.perf_counter() - t0) * 1000)
            res_count = len(sources)
            top_score = sources[0].relevance_score if sources else 0.0
        avg_t = sum(times) / len(times)
        print(f"  [{q_type}] '{q_text[:40]}...' -> {res_count} sources, top score: {top_score:.3f}, avg latency: {avg_t:.2f} ms")

    # 6. Test Ollama Inference Latency (Streaming TTFT & Generation)
    print("\n--- 4. Ollama Local LLM Latency & Throughput (qwen2.5:3b) ---")
    prompt_messages = [
        {"role": "system", "content": "You are BharatInsure AI. Answer in 2 short bullet points."},
        {"role": "user", "content": "What is the initial waiting period in health insurance?"}
    ]

    print("Measuring streaming performance (TTFT, tokens/sec)...")
    tokens = []
    t_start = time.perf_counter()
    first_token_latency = None
    stream_gen = local_llm_service.generate_stream(prompt_messages, max_new_tokens=80)
    for chunk, ttft, done in stream_gen:
        if chunk and first_token_latency is None:
            first_token_latency = (time.perf_counter() - t_start) * 1000
        if chunk:
            tokens.append(chunk)

    total_stream_latency = (time.perf_counter() - t_start) * 1000
    full_text = "".join(tokens)
    token_count = len(tokens)
    tps = (token_count / (total_stream_latency / 1000)) if total_stream_latency > 0 else 0
    print(f"  Time To First Token (TTFT): {first_token_latency:.1f} ms")
    print(f"  Total Stream Time: {total_stream_latency:.1f} ms")
    print(f"  Generated Chunks/Tokens: ~{token_count}")
    print(f"  Throughput: {tps:.2f} tokens/sec")
    print(f"  Sample Output: {full_text[:120].strip()}...")

    # Also test non-streaming generate()
    print("\nMeasuring standard non-streaming generate()...")
    gen_res = local_llm_service.generate(prompt_messages, max_new_tokens=80)
    print(f"  Latency: {gen_res.get('latency_ms')} ms")
    print(f"  Tokens Generated: {gen_res.get('tokens_generated')}")
    print(f"  Tokens/Sec: {gen_res.get('tokens_per_sec')}")

    # 7. End-to-End LLMManager Generation Latency
    print("\n--- 5. End-to-End Full Chat Turn Latency ---")
    e2e_queries = [
        ("Greeting without filter", "Hello"),
        ("Finance domain query", "What is the pre-existing disease waiting period?")
    ]
    for q_name, q_val in e2e_queries:
        lang, _ = LanguageDetector.detect(q_val)
        srcs = rag_retriever.retrieve(q_val, top_k=3)
        t0 = time.perf_counter()
        resp = llm_manager.generate_response(
            query=q_val,
            detected_language=lang,
            sources=srcs,
            conversation_history_text="",
            model_preference="local_small"
        )
        total_e2e = (time.perf_counter() - t0) * 1000
        print(f"  [{q_name}] Model used: {resp['model_used']}, Total Latency: {total_e2e:.1f} ms")

if __name__ == "__main__":
    run_audit()
