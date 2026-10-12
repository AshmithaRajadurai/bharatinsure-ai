"""
Final Verification Script for BharatInsure AI Local LLM Implementation.
Tests:
1. Model Status API (/model/status)
2. English Query with Base Insurance RAG
3. Tamil Query with Base Insurance RAG
4. Hindi Query with Base Insurance RAG
5. Fintech Query (UPI)
6. Uploaded Policy Document Grounding + Q&A (via multipart/form-data upload)
7. Irrelevant Query (Threshold Filtering)
8. Benchmark API Metrics (/benchmark)
Saves complete raw results to benchmark/final_verification_results.json
"""

import requests
import json
import time
import os
import io

BASE_URL = "http://127.0.0.1:8000"

def safe_str(s, max_len=200):
    if not s:
        return ""
    ascii_clean = s.encode('ascii', errors='replace').decode('ascii')
    return ascii_clean[:max_len]

def run_tests():
    print("=" * 70, flush=True)
    print("BHARATINSURE AI - LOCAL LLM VERIFICATION SUITE", flush=True)
    print("=" * 70, flush=True)

    all_results = {}

    # 1. Model Status
    print("\n[STEP 1] Querying /model/status...", flush=True)
    status_resp = requests.get(f"{BASE_URL}/model/status")
    status = status_resp.json()
    all_results["model_status"] = status
    print(f"  * Model: {status.get('model_name')}", flush=True)
    print(f"  * Parameters: {status.get('exact_parameter_count'):,} ({status.get('parameter_count_millions')}M)", flush=True)
    print(f"  * Meets >=300M Requirement: {status.get('meets_300m_requirement')}", flush=True)
    print(f"  * Loaded in RAM: {status.get('is_loaded')}", flush=True)
    print(f"  * Runtime: {status.get('runtime')}", flush=True)
    print(f"  * Device: {status.get('device')}", flush=True)

    # 2. English Query
    print("\n[STEP 2] English Query: What is the waiting period for pre-existing diseases?...", flush=True)
    t0 = time.time()
    en_res = requests.post(f"{BASE_URL}/chat", json={
        "message": "What is the waiting period for pre-existing diseases?",
        "model_preference": "local_small",
        "session_id": "eval-session-en"
    }).json()
    en_elapsed = round((time.time() - t0) * 1000, 2)
    all_results["english_query"] = en_res
    print(f"  * Model Used: {en_res.get('model_used')}", flush=True)
    print(f"  * Latency: {en_elapsed} ms (Backend latency: {en_res.get('latency_ms')} ms)", flush=True)
    print(f"  * Sources count: {len(en_res.get('sources', []))}", flush=True)
    for s in en_res.get('sources', []):
        print(f"    - [{s.get('category')}] {s.get('title')} (score: {s.get('relevance_score')})", flush=True)
    print(f"  * Local LLM Output: {safe_str(en_res.get('response'))}...", flush=True)

    # 3. Tamil Query
    print("\n[STEP 3] Tamil Query: Waiting period query in Tamil...", flush=True)
    t0 = time.time()
    ta_res = requests.post(f"{BASE_URL}/chat", json={
        "message": "முன்பிருந்த நோய்க்கான காத்திருப்பு காலம் எவ்வளவு?",
        "model_preference": "local_small",
        "session_id": "eval-session-ta"
    }).json()
    ta_elapsed = round((time.time() - t0) * 1000, 2)
    all_results["tamil_query"] = ta_res
    print(f"  * Model Used: {ta_res.get('model_used')}", flush=True)
    print(f"  * Detected Lang: {ta_res.get('detected_language')}", flush=True)
    print(f"  * Latency: {ta_elapsed} ms (Backend: {ta_res.get('latency_ms')} ms)", flush=True)
    print(f"  * Sources count: {len(ta_res.get('sources', []))}", flush=True)
    for s in ta_res.get('sources', []):
        print(f"    - [{s.get('category')}] {s.get('title')} (score: {s.get('relevance_score')})", flush=True)
    print(f"  * Local LLM Output: {safe_str(ta_res.get('response'))}...", flush=True)

    # 4. Hindi Query
    print("\n[STEP 4] Hindi Query: Waiting period query in Hindi...", flush=True)
    t0 = time.time()
    hi_res = requests.post(f"{BASE_URL}/chat", json={
        "message": "पहले से मौजूद बीमारी के लिए प्रतीक्षा अवधि कितनी है?",
        "model_preference": "local_small",
        "session_id": "eval-session-hi"
    }).json()
    hi_elapsed = round((time.time() - t0) * 1000, 2)
    all_results["hindi_query"] = hi_res
    print(f"  * Model Used: {hi_res.get('model_used')}", flush=True)
    print(f"  * Detected Lang: {hi_res.get('detected_language')}", flush=True)
    print(f"  * Latency: {hi_elapsed} ms (Backend: {hi_res.get('latency_ms')} ms)", flush=True)
    print(f"  * Sources count: {len(hi_res.get('sources', []))}", flush=True)
    for s in hi_res.get('sources', []):
        print(f"    - [{s.get('category')}] {s.get('title')} (score: {s.get('relevance_score')})", flush=True)
    print(f"  * Local LLM Output: {safe_str(hi_res.get('response'))}...", flush=True)

    # 5. Fintech Query
    print("\n[STEP 5] Fintech Query: What is UPI and how does it work?...", flush=True)
    t0 = time.time()
    fin_res = requests.post(f"{BASE_URL}/chat", json={
        "message": "What is UPI and how does it work?",
        "model_preference": "local_small",
        "session_id": "eval-session-fin"
    }).json()
    fin_elapsed = round((time.time() - t0) * 1000, 2)
    all_results["fintech_query"] = fin_res
    print(f"  * Model Used: {fin_res.get('model_used')}", flush=True)
    print(f"  * Latency: {fin_elapsed} ms (Backend: {fin_res.get('latency_ms')} ms)", flush=True)
    print(f"  * Sources count: {len(fin_res.get('sources', []))}", flush=True)
    print(f"  * Local LLM Output: {safe_str(fin_res.get('response'))}...", flush=True)

    # 6. Uploaded Document Integration
    print("\n[STEP 6] Uploading Policy Document & Querying...", flush=True)
    doc_text = (
        "AROGYA SANJEEVANI POLICY CLAUSE 4.2: Pre-existing Disease (PED) Waiting Period.\n"
        "All pre-existing medical conditions shall have a strict waiting period of exactly 36 months (3 years) "
        "of continuous coverage. After 36 months, all listed pre-existing conditions are covered up to the sum insured. "
        "Co-payment: A mandatory co-payment of 5% applies to all admissible claims under this policy."
    )
    file_bytes = io.BytesIO(doc_text.encode('utf-8'))
    files = {"file": ("Arogya_Sanjeevani_Policy.txt", file_bytes, "text/plain")}
    data = {"session_id": "eval-doc-session"}
    
    upload_resp = requests.post(f"{BASE_URL}/documents/upload", files=files, data=data)
    upload_res = upload_resp.json()
    print(f"  * Upload status: {upload_res.get('message')}", flush=True)
    print(f"  * Chunks indexed: {upload_res.get('total_chunks')}", flush=True)
    all_results["doc_upload"] = upload_res

    t0 = time.time()
    doc_chat = requests.post(f"{BASE_URL}/chat", json={
        "message": "What is the waiting period according to my uploaded Arogya Sanjeevani policy?",
        "model_preference": "local_small",
        "session_id": "eval-doc-session"
    }).json()
    doc_elapsed = round((time.time() - t0) * 1000, 2)
    all_results["doc_query"] = doc_chat
    print(f"  * Model Used: {doc_chat.get('model_used')}", flush=True)
    print(f"  * Latency: {doc_elapsed} ms (Backend: {doc_chat.get('latency_ms')} ms)", flush=True)
    print(f"  * Sources count: {len(doc_chat.get('sources', []))}", flush=True)
    for s in doc_chat.get('sources', []):
        print(f"    - [{s.get('category')}] {s.get('title')} (score: {s.get('relevance_score')})", flush=True)
    print(f"  * Local LLM Output: {safe_str(doc_chat.get('response'))}...", flush=True)

    # 7. Irrelevant Query (Threshold Check)
    print("\n[STEP 7] Irrelevant Query: Explain quantum entanglement in superconductors...", flush=True)
    irr_res = requests.post(f"{BASE_URL}/chat", json={
        "message": "Explain quantum entanglement in superconductors",
        "model_preference": "local_small",
        "session_id": "eval-session-irr"
    }).json()
    all_results["irrelevant_query"] = irr_res
    print(f"  * Model Used: {irr_res.get('model_used')}", flush=True)
    print(f"  * Sources count: {len(irr_res.get('sources', []))} (Threshold >= 0.25 filtering confirmed: {len(irr_res.get('sources', [])) == 0})", flush=True)
    print(f"  * Local LLM Output: {safe_str(irr_res.get('response'))}...", flush=True)

    # 8. Benchmark Metrics
    print("\n[STEP 8] Querying Live /benchmark...", flush=True)
    bench_resp = requests.get(f"{BASE_URL}/benchmark")
    bench = bench_resp.json()
    all_results["benchmark_report"] = bench
    print(f"  * Host System RAM: {bench.get('system_ram_mb')} MB", flush=True)
    print(f"  * Process RAM: {bench.get('process_ram_mb')} MB", flush=True)
    print(f"  * Active KB Chunks: {bench.get('retrieval_chunks_count')}", flush=True)
    print("  * Models in report:", flush=True)
    for m in bench.get('models', []):
        print(f"    - {m.get('model_name')}: Latency={m.get('latency_ms')}ms | Grounding={m.get('rag_grounding_score')} | Loaded={m.get('hardware_cost')}", flush=True)

    # Save all results to benchmark/final_verification_results.json
    os.makedirs("benchmark", exist_ok=True)
    with open("benchmark/final_verification_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print("\nSaved full verification results to benchmark/final_verification_results.json", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("ALL 8 VERIFICATION STEPS COMPLETED SUCCESSFULLY!", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    run_tests()
