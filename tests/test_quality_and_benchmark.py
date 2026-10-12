"""
BharatInsure AI — Quality & Speed Benchmark Suite
Verifies:
1. 6 Specific Factual & Relevance Questions
2. 5 Repeated Benchmark Iterations for English, Tamil, and Hindi
3. Cold vs Warm latency, TTFT, Tokens/sec, RAM consumption
"""

import sys
import os
import time
import json
import urllib.request
import requests
import psutil

# Ensure current working directory is on sys.path
sys.path.insert(0, os.path.abspath("."))
# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"
OLLAMA_URL = "http://localhost:11434"

def get_ram_usage():
    """Returns memory usage in MB for backend process and ollama processes."""
    backend_mb = 0.0
    ollama_mb = 0.0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            name = (proc.info['name'] or "").lower()
            cmd = " ".join(proc.info['cmdline'] or []).lower()
            mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
            if "uvicorn" in cmd or ("python" in name and "backend.main" in cmd):
                backend_mb += mem_mb
            if "ollama" in name or "ollama" in cmd:
                ollama_mb += mem_mb
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return round(backend_mb, 1), round(ollama_mb, 1)

def run_factual_and_relevance_checks():
    print("=" * 80)
    print("SECTION 6: FACTUAL AND RELEVANCE CHECKS (6 QUESTIONS)")
    print("=" * 80)

    # 1. Clean session
    session_id = "test-session-eval-01"

    # Test 1: What is the waiting period for pre-existing diseases?
    print("\n--- [Question 1] Pre-Existing Diseases Waiting Period ---")
    t0 = time.time()
    r1 = requests.post(f"{BASE_URL}/chat", json={
        "message": "What is the waiting period for pre-existing diseases?",
        "session_id": session_id,
        "language": "en",
        "model_preference": "local_small"
    }).json()
    t1 = time.time()
    print(f"Latency: {round((t1 - t0)*1000, 1)}ms | Model: {r1.get('model_used')}")
    print(f"Sources returned: {len(r1.get('sources', []))}")
    for s in r1.get('sources', []):
        print(f"  - [{s.get('id')}] {s.get('title')} (score: {s.get('relevance_score')})")
    print(f"Answer:\n{r1.get('response')}\n")

    # Verify no maternity chunk in sources
    source_ids = [s.get('id') for s in r1.get('sources', [])]
    assert "health-06" not in source_ids, "ERROR: Maternity chunk should NOT be in PED response!"
    assert any("health-02" in sid for sid in source_ids), "ERROR: health-02 (PED) must be retrieved!"

    # Test 2: What is the maternity waiting period?
    print("\n--- [Question 2] Maternity Waiting Period ---")
    t0 = time.time()
    r2 = requests.post(f"{BASE_URL}/chat", json={
        "message": "What is the maternity waiting period?",
        "session_id": session_id,
        "language": "en",
        "model_preference": "local_small"
    }).json()
    t1 = time.time()
    print(f"Latency: {round((t1 - t0)*1000, 1)}ms | Model: {r2.get('model_used')}")
    print(f"Sources returned: {len(r2.get('sources', []))}")
    for s in r2.get('sources', []):
        print(f"  - [{s.get('id')}] {s.get('title')} (score: {s.get('relevance_score')})")
    print(f"Answer:\n{r2.get('response')}\n")

    source_ids2 = [s.get('id') for s in r2.get('sources', [])]
    assert "health-06" in source_ids2, "ERROR: Maternity chunk must be retrieved!"

    # Test 3: What is UPI?
    print("\n--- [Question 3] What is UPI? ---")
    t0 = time.time()
    r3 = requests.post(f"{BASE_URL}/chat", json={
        "message": "What is UPI?",
        "session_id": session_id,
        "language": "en",
        "model_preference": "local_small"
    }).json()
    t1 = time.time()
    print(f"Latency: {round((t1 - t0)*1000, 1)}ms | Model: {r3.get('model_used')}")
    print(f"Sources returned: {len(r3.get('sources', []))}")
    for s in r3.get('sources', []):
        print(f"  - [{s.get('id')}] {s.get('title')} (score: {s.get('relevance_score')})")
    print(f"Answer:\n{r3.get('response')}\n")
    source_ids3 = [s.get('id') for s in r3.get('sources', [])]
    assert any("fintech" in sid for sid in source_ids3), "ERROR: Fintech UPI chunk must be retrieved!"

    # Test 4: Explain cashless health insurance in simple words.
    print("\n--- [Question 4] Explain cashless health insurance in simple words ---")
    t0 = time.time()
    r4 = requests.post(f"{BASE_URL}/chat", json={
        "message": "Explain cashless health insurance in simple words.",
        "session_id": session_id,
        "language": "en",
        "model_preference": "local_small"
    }).json()
    t1 = time.time()
    print(f"Latency: {round((t1 - t0)*1000, 1)}ms | Model: {r4.get('model_used')}")
    print(f"Sources returned: {len(r4.get('sources', []))}")
    for s in r4.get('sources', []):
        print(f"  - [{s.get('id')}] {s.get('title')} (score: {s.get('relevance_score')})")
    print(f"Answer:\n{r4.get('response')}\n")
    source_ids4 = [s.get('id') for s in r4.get('sources', [])]
    assert "health-05" in source_ids4, "ERROR: health-05 (Cashless vs Reimbursement) must be retrieved!"

    # Test 5: Ask a question answered specifically by an uploaded policy document.
    print("\n--- [Question 5] Upload Policy Document & Ask Specific Question ---")
    upload_session = "test-doc-upload-session"
    pdf_path = "tests/sample_docs/HDFC_Optima_Secure_Policy.pdf"
    with open(pdf_path, "rb") as f:
        up_resp = requests.post(
            f"{BASE_URL}/documents/upload",
            files={"file": ("HDFC_Optima_Secure_Policy.pdf", f, "application/pdf")},
            data={"session_id": upload_session}
        ).json()
    print(f"Document uploaded: {up_resp.get('document_name')} ({up_resp.get('total_pages')} pages, {up_resp.get('total_chunks')} chunks)")

    # Query a feature specific to this policy: Air Ambulance or Waiting Period in uploaded doc
    t0 = time.time()
    r5 = requests.post(f"{BASE_URL}/chat", json={
        "message": "What is the pre-existing disease waiting period in my uploaded HDFC Optima Secure policy?",
        "session_id": upload_session,
        "language": "en",
        "model_preference": "local_small"
    }).json()
    t1 = time.time()
    print(f"Latency: {round((t1 - t0)*1000, 1)}ms | Model: {r5.get('model_used')}")
    print(f"Active Document: {r5.get('active_document')}")
    print(f"Sources returned: {len(r5.get('sources', []))}")
    for s in r5.get('sources', []):
        print(f"  - [{s.get('source_type')}] {s.get('title')} (score: {s.get('relevance_score')}, page: {s.get('page')})")
    print(f"Answer:\n{r5.get('response')}\n")
    doc_sources = [s for s in r5.get('sources', []) if s.get('source_type') == "uploaded_document"]
    assert len(doc_sources) > 0, "ERROR: Uploaded document chunks must be retrieved!"

    # Test 6: Ask an unrelated question outside insurance/fintech knowledge base
    print("\n--- [Question 6] Unrelated Question Outside Knowledge Base ---")
    t0 = time.time()
    r6 = requests.post(f"{BASE_URL}/chat", json={
        "message": "What is quantum entanglement and quantum teleportation?",
        "session_id": session_id,
        "language": "en",
        "model_preference": "local_small"
    }).json()
    t1 = time.time()
    print(f"Latency: {round((t1 - t0)*1000, 1)}ms | Model: {r6.get('model_used')}")
    print(f"Sources returned: {len(r6.get('sources', []))}")
    print(f"Answer:\n{r6.get('response')}\n")
    assert len(r6.get('sources', [])) == 0, "ERROR: Unrelated question must NOT retrieve insurance chunks!"
    assert "couldn't find" in r6.get('response').lower() or "outside" in r6.get('response').lower() or "specialized" in r6.get('response').lower(), "ERROR: Expected limitation message!"

    print("ALL 6 FACTUAL AND RELEVANCE CHECKS PASSED SUCCESSFULLY!\n")


def benchmark_language(lang_code, lang_name, query, iterations=5):
    print("=" * 80)
    print(f"BENCHMARK: {lang_name.upper()} ({lang_code}) — {iterations} REPEATED ITERATIONS")
    print(f"Query: {query}")
    print("=" * 80)

    from backend.services.rag.retriever import rag_retriever
    from backend.services.llm.local_model_service import local_llm_service
    from backend.services.language.detector import LanguageDetector

    results = []
    lang_info = LanguageDetector.get_language_info(lang_code)

    for i in range(1, iterations + 1):
        # 1. Measure RAG Retrieval Time
        t_rag_start = time.time()
        sources = rag_retriever.retrieve(query=query, top_k=3)
        rag_time_ms = round((time.time() - t_rag_start) * 1000, 2)

        # 2. Build Context and Prompt
        context_str = "\n".join([f"- [{s.title}]: {s.snippet}" for s in sources])
        prompt_system = f"""You are BharatInsure AI, an expert Indian fintech and insurance conversational assistant.
Answer in {lang_info['name']} ({lang_info['native']}).

RESPONSE STYLE RULES:
1. Start directly with a simple 1-sentence answer. No fluff, no repeating the question.
2. Provide 2-3 short numbered points using simple, beginner-friendly words. Explain technical terms briefly.
3. Answer ONLY what was asked. Never combine unrelated topics.
4. Ground your answer strictly in the Retrieved Evidence below. Never invent waiting periods, figures, or benefits.
5. End with: "Remember: Check your policy document for the exact duration and terms."
6. Target length: approximately 60-110 words.

Retrieved Factual Evidence:
{context_str}"""

        messages = [
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": query}
        ]

        # 3. Measure Streaming Inference (Time to First Token + Total Tokens + Latency)
        t_stream_start = time.time()
        measured_ttft_ms = None
        full_tokens = []

        for content, ttft, done in local_llm_service.generate_stream(messages, max_new_tokens=130):
            if ttft is not None and measured_ttft_ms is None:
                measured_ttft_ms = ttft
            if content:
                full_tokens.append(content)

        t_total_end = time.time()

        ttft_ms = measured_ttft_ms or round((t_total_end - t_stream_start) * 1000, 2)
        total_time_ms = round((t_total_end - t_stream_start) * 1000, 2)
        total_resp_time_ms = round(rag_time_ms + total_time_ms, 2)
        generated_text = "".join(full_tokens)
        token_count = len(generated_text.split()) # Approx word tokens or estimate
        gen_duration_sec = max(0.05, total_time_ms / 1000.0)
        tps = round(token_count / gen_duration_sec, 2)

        backend_ram, ollama_ram = get_ram_usage()

        res_item = {
            "iteration": i,
            "is_cold": (i == 1),
            "rag_time_ms": rag_time_ms,
            "ttft_ms": ttft_ms,
            "total_gen_ms": total_time_ms,
            "total_response_ms": total_resp_time_ms,
            "word_count": token_count,
            "approx_tokens_per_sec": tps,
            "backend_ram_mb": backend_ram,
            "ollama_ram_mb": ollama_ram,
            "total_ram_mb": round(backend_ram + ollama_ram, 1),
            "response_sample": generated_text.strip()[:160] + "..."
        }
        results.append(res_item)
        print(f"Iter {i}{' (Cold)' if i == 1 else ' (Warm)'}: RAG={rag_time_ms}ms | TTFT={ttft_ms}ms | Total={total_resp_time_ms}ms | Words={token_count} | {tps} words/s | RAM={round(backend_ram + ollama_ram, 1)}MB")

    return results

def main():
    # 1. Run factual checks
    run_factual_and_relevance_checks()

    # 2. English Benchmark
    en_results = benchmark_language(
        lang_code="en",
        lang_name="English",
        query="What is the waiting period for pre-existing diseases?",
        iterations=5
    )

    # 3. Tamil Benchmark
    ta_results = benchmark_language(
        lang_code="ta",
        lang_name="Tamil",
        query="முன்பிருந்த நோய்களுக்கான காத்திருப்பு காலம் என்ன?",
        iterations=5
    )

    # 4. Hindi Benchmark
    hi_results = benchmark_language(
        lang_code="hi",
        lang_name="Hindi",
        query="पहले से मौजूद बीमारियों के लिए प्रतीक्षा अवधि क्या है?",
        iterations=5
    )

    # Save summary artifact
    summary = {
        "en": en_results,
        "ta": ta_results,
        "hi": hi_results
    }
    with open("benchmark_results_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print("\nBenchmark results saved to benchmark_results_summary.json")

if __name__ == "__main__":
    main()
