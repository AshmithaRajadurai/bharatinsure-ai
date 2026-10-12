"""
End-to-End Verification Test Script for BharatInsure AI
Validates all requirements and the Demo Scenario (Section 20).
"""

import sys
import json
import urllib.request
import urllib.error

# Ensure UTF-8 printing on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"

def post_json(path, data):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def get_json(path):
    with urllib.request.urlopen(f"{BASE_URL}{path}") as response:
        return json.loads(response.read().decode("utf-8"))

def run_tests():
    print("=" * 60)
    print("🚀 BHARATINSURE AI – COMPREHENSIVE VERIFICATION SUITE")
    print("=" * 60)

    # 1. Health Check
    health = get_json("/health")
    print(f"\n[1] Health Check: {health['status']} | Languages: {len(health['supported_languages'])}")
    assert health["status"] == "healthy"

    # 2. Languages Check
    langs = get_json("/languages")
    print(f"[2] Supported Languages Count: {len(langs['languages'])}")
    for l in langs["languages"][:6]:
        print(f"    - {l['flag']} {l['name']} ({l['native']}) [code: {l['code']}, STT: {l['stt_code']}]")

    session_id = "demo-test-session-101"

    # 3. STEP 1: English Turn
    print("\n--- DEMO STEP 1: User asks in English ---")
    step1_req = {
        "message": "What is health insurance?",
        "session_id": session_id,
        "language": "auto",
        "model_preference": "api",
        "input_type": "text"
    }
    step1_res = post_json("/chat", step1_req)
    print(f"User [en]: {step1_req['message']}")
    print(f"Detected Lang: {step1_res['detected_language']} ({step1_res['language_name']})")
    print(f"Model Used: {step1_res['model_used']} | Latency: {step1_res['latency_ms']}ms")
    print(f"RAG Sources: {len(step1_res['sources'])} retrieved chunks")
    for s in step1_res["sources"]:
        print(f"   * [{s['category']}] {s['title']} (Score: {s['relevance_score']})")
    print(f"Assistant Response Snippet:\n   {step1_res['response'][:150]}...")
    assert step1_res["detected_language"] == "en"
    assert len(step1_res["sources"]) > 0

    # 4. STEP 2: Tamil Turn (Voice / Text)
    print("\n--- DEMO STEP 2: User speaks/enters in Tamil ---")
    step2_req = {
        "message": "ஹெல்த் இன்சூரன்ஸ் என்றால் என்ன?",
        "session_id": session_id,
        "language": "auto",
        "model_preference": "api",
        "input_type": "voice"
    }
    step2_res = post_json("/chat", step2_req)
    print(f"User [ta]: {step2_req['message']}")
    print(f"Detected Lang: {step2_res['detected_language']} ({step2_res['language_name']})")
    print(f"RAG Sources: {len(step2_res['sources'])} retrieved chunks")
    for s in step2_res["sources"]:
        print(f"   * [{s['category']}] {s['title']} (Score: {s['relevance_score']})")
    print(f"Assistant Response:\n   {step2_res['response'][:180]}...")
    assert step2_res["detected_language"] == "ta"

    # 5. STEP 3: Hindi Turn
    print("\n--- DEMO STEP 3: User speaks/enters in Hindi ---")
    step3_req = {
        "message": "मुझे स्वास्थ्य बीमा के बारे में जानकारी चाहिए",
        "session_id": session_id,
        "language": "auto",
        "model_preference": "api",
        "input_type": "voice"
    }
    step3_res = post_json("/chat", step3_req)
    print(f"User [hi]: {step3_req['message']}")
    print(f"Detected Lang: {step3_res['detected_language']} ({step3_res['language_name']})")
    print(f"Assistant Response:\n   {step3_res['response'][:180]}...")
    assert step3_res["detected_language"] == "hi"

    # 6. STEP 4: Switch back to Tamil with Conversation Memory retention
    print("\n--- DEMO STEP 4: User changes back to Tamil with Anaphoric Query ---")
    step4_req = {
        "message": "காத்திருப்பு காலம் எவ்வளவு?",
        "session_id": session_id,
        "language": "auto",
        "model_preference": "local_small",
        "input_type": "text"
    }
    step4_res = post_json("/chat", step4_req)
    print(f"User [ta]: {step4_req['message']} (Asking: 'What is the waiting period?')")
    print(f"Detected Lang: {step4_res['detected_language']} ({step4_res['language_name']})")
    print(f"Model Preference: Small Local Model -> {step4_res['model_used']}")
    print(f"Assistant Response:\n   {step4_res['response'][:220]}...")
    assert step4_res["detected_language"] == "ta"
    # Check that waiting period and health context was understood
    assert "காத்திருப்பு" in step4_res["response"] or "மாதங்கள்" in step4_res["response"]

    # 7. STEP 5 & 6: RAG Transparency Inspection
    print("\n--- DEMO STEP 6: Direct RAG Knowledge Base Retrieval Inspection ---")
    rag_inspect = post_json("/retrieve", {"query": "third party vs zero depreciation motor insurance", "top_k": 3})
    print(f"Query: '{rag_inspect['query']}'")
    for r in rag_inspect["results"]:
        print(f"   * [{r['category']}] {r['title']} | Score: {r['relevance_score']}")
    assert len(rag_inspect["results"]) > 0

    # 8. STEP 7: Benchmark & Efficiency Evaluation
    print("\n--- DEMO STEP 7: Small Model Efficiency & Live Benchmark ---")
    benchmark_data = get_json("/benchmark")
    print(f"Benchmark Criteria: {len(benchmark_data['evaluation_criteria'])} dimensions")
    for m in benchmark_data["models"]:
        print(f"\nModel: {m['model_name']}")
        print(f"  - Size: {m['model_size']}")
        print(f"  - Peak RAM: {m['ram_usage']}")
        print(f"  - Tamil Quality: {m['tamil_quality']}")
        print(f"  - Hindi Quality: {m['hindi_quality']}")
        print(f"  - RAG Accuracy: {m['rag_accuracy']}")

    print("\nRunning Live Host Benchmark...")
    live_res = post_json("/benchmark/run-live", {})
    print(f"Live Test Success: {live_res['status']} | Available Host RAM: {live_res['system_ram_available_mb']} MB")
    for lm in live_res["live_metrics"]:
        print(f"  - [{lm['language'].upper()}] Total Latency: {lm['total_latency_ms']}ms (RAG: {lm['rag_latency_ms']}ms, LLM: {lm['llm_latency_ms']}ms) | Process RAM: {lm['ram_used_mb']} MB")

    # 9. Text-to-Speech Test
    print("\n--- TTS AUDIO SYNTHESIS TEST ---")
    tts_test = post_json("/text-to-speech", {"text": "வணக்கம்! பாரத் இன்சூரன்ஸ்", "language": "ta"})
    print(f"Tamil TTS Synthesis: Success={tts_test['success']} | Latency={tts_test['latency_ms']}ms | Audio Bytes Received={len(tts_test.get('audio_base64', '') or '') > 0}")
    assert tts_test["success"] == True

    print("\n" + "=" * 60)
    print("✅ ALL 7 DEMO STEPS & VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
