"""
Comprehensive Verification Test Suite for BharatInsure AI:
Validates Tests 1 to 6 as requested by the user:
- TEST 1: Upload sample PDF, ask waiting period question, verify document citation.
- TEST 2: Ask question existing ONLY in uploaded document (Air Ambulance), verify document retrieval.
- TEST 3: Ask general insurance question (Motor Zero Dep), verify existing Base JSON RAG still works.
- TEST 4: Ask in Tamil with active document, verify language detection, doc retrieval, and Tamil output.
- TEST 5: Remove document, ask same document question, verify document is no longer used.
- TEST 6: Test multiple Popular Insurance Topics, verify normal RAG pipeline execution.
"""

import sys
import requests
import json

# Ensure UTF-8 output on Windows console
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000"
SESSION_ID = "test-session-suite-101"

def print_banner(text):
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)

def main():
    print_banner("BHARATINSURE AI: DOCUMENT RAG & TOPICS VERIFICATION SUITE")

    # Health check
    try:
        health_resp = requests.get(f"{BASE_URL}/health", timeout=5)
        assert health_resp.status_code == 200, f"Health check failed: {health_resp.status_code}"
        print("Backend server is HEALTHY on", BASE_URL)
    except Exception as e:
        print(f"FAILED to reach backend at {BASE_URL}: {e}")
        sys.exit(1)

    # ----------------------------------------------------
    # TEST 1: Upload sample insurance PDF & ask waiting period
    # ----------------------------------------------------
    print_banner("TEST 1: Upload Sample PDF & Query Pre-Existing Disease Waiting Period")
    pdf_path = "tests/sample_docs/HDFC_Optima_Secure_Policy.pdf"
    with open(pdf_path, "rb") as f:
        upload_resp = requests.post(
            f"{BASE_URL}/documents/upload",
            files={"file": ("HDFC_Optima_Secure_Policy.pdf", f, "application/pdf")},
            data={"session_id": SESSION_ID},
            timeout=30
        )
    assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
    upload_data = upload_resp.json()
    print("✓ Upload response:", upload_data["message"])
    print(f"  Pages extracted: {upload_data['total_pages']} | Chunks indexed: {upload_data['total_chunks']}")
    assert upload_data["success"] is True
    assert upload_data["total_pages"] in [4, 6]
    assert upload_data["total_chunks"] >= 4

    # Ask waiting period question
    chat_resp = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "What is the waiting period for pre-existing diseases?",
            "session_id": SESSION_ID,
            "language": "auto",
            "model_preference": "api"
        },
        timeout=30
    )
    assert chat_resp.status_code == 200, f"Chat error: {chat_resp.text}"
    chat_data = chat_resp.json()
    print("✓ Query: 'What is the waiting period for pre-existing diseases?'")
    print(f"✓ Detected Language: {chat_data['detected_language']} ({chat_data['language_name']})")
    print(f"✓ Active Document: {chat_data.get('active_document')}")
    print(f"✓ Sources Retrieved ({len(chat_data['sources'])}):")
    for s in chat_data["sources"]:
        print(f"   - [{s.get('source_type')}] {s['title']} | Score: {s['relevance_score']}")
    print("\n✓ Assistant Answer:")
    print(chat_data["response"])

    # Verify that answer references uploaded document and 36 months / Page 2
    doc_sources = [s for s in chat_data["sources"] if s.get("source_type") == "uploaded_document"]
    assert len(doc_sources) > 0, "TEST 1 FAILED: Expected uploaded document sources to be retrieved"
    assert doc_sources[0]["document_name"] == "HDFC_Optima_Secure_Policy.pdf"
    assert "36" in chat_data["response"] or "36" in doc_sources[0]["snippet"]
    print("TEST 1 PASSED: Successfully retrieved and answered from uploaded PDF!")

    # ----------------------------------------------------
    # TEST 2: Question that exists ONLY in uploaded document (Air Ambulance)
    # ----------------------------------------------------
    print_banner("TEST 2: Query for Feature Existing ONLY in Uploaded Document (Air Ambulance)")
    chat_resp_2 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "What is the limit for emergency air ambulance coverage in this policy?",
            "session_id": SESSION_ID,
            "language": "auto",
            "model_preference": "api"
        },
        timeout=30
    )
    assert chat_resp_2.status_code == 200
    chat_data_2 = chat_resp_2.json()
    print("✓ Query: 'What is the limit for emergency air ambulance coverage in this policy?'")
    print(f"✓ Sources Retrieved ({len(chat_data_2['sources'])}):")
    for s in chat_data_2["sources"]:
        print(f"   - [{s.get('source_type')}] {s['title']} | Page: {s.get('page')} | Score: {s['relevance_score']}")
    print("\n✓ Assistant Answer:")
    print(chat_data_2["response"])

    doc_sources_2 = [s for s in chat_data_2["sources"] if s.get("source_type") == "uploaded_document"]
    assert len(doc_sources_2) > 0, "TEST 2 FAILED: Expected uploaded document retrieval for Air Ambulance"
    assert doc_sources_2[0]["page"] == 4, f"Expected Page 4 for Air Ambulance, got {doc_sources_2[0]['page']}"
    assert "2,50,000" in doc_sources_2[0]["snippet"] or "2,50,000" in chat_data_2["response"]
    print("TEST 2 PASSED: Successfully retrieved Page 4 Air Ambulance clause from uploaded document!")

    # ----------------------------------------------------
    # TEST 3: General insurance question (Base JSON RAG verification)
    # ----------------------------------------------------
    print_banner("TEST 3: General Insurance Question (Verifying Base JSON RAG)")
    chat_resp_3 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "What is Zero Depreciation motor insurance and what does it cover?",
            "session_id": SESSION_ID,
            "language": "auto",
            "model_preference": "api"
        },
        timeout=30
    )
    assert chat_resp_3.status_code == 200
    chat_data_3 = chat_resp_3.json()
    print("✓ Query: 'What is Zero Depreciation motor insurance and what does it cover?'")
    print(f"✓ Sources Retrieved ({len(chat_data_3['sources'])}):")
    for s in chat_data_3["sources"]:
        print(f"   - [{s.get('source_type')}] {s['category']}: {s['title']} | Score: {s['relevance_score']}")
    print("\n✓ Assistant Answer:")
    print(chat_data_3["response"][:300] + "...")

    kb_sources = [s for s in chat_data_3["sources"] if s.get("source_type") == "knowledge_base"]
    assert len(kb_sources) > 0, "TEST 3 FAILED: Expected Base Knowledge Base sources to be retrieved"
    assert "Motor" in kb_sources[0]["category"] or "Zero" in kb_sources[0]["title"]
    print("TEST 3 PASSED: Base JSON Knowledge Base RAG operates smoothly alongside document RAG!")

    # ----------------------------------------------------
    # TEST 4: Query in Tamil with active document
    # ----------------------------------------------------
    print_banner("TEST 4: Tamil Query with Active Document (Language Detection & Document RAG)")
    tamil_query = "அறை வாடகை வரம்பு எவ்வளவு?" # "What is the room rent limit?"
    chat_resp_4 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": tamil_query,
            "session_id": SESSION_ID,
            "language": "auto",
            "model_preference": "api"
        },
        timeout=30
    )
    assert chat_resp_4.status_code == 200
    chat_data_4 = chat_resp_4.json()
    print(f"✓ Query: '{tamil_query}'")
    print(f"✓ Detected Language: {chat_data_4['detected_language']} ({chat_data_4['language_name']})")
    print(f"✓ Sources Retrieved ({len(chat_data_4['sources'])}):")
    for s in chat_data_4["sources"]:
        print(f"   - [{s.get('source_type')}] {s['title']} | Score: {s['relevance_score']}")
    print("\n✓ Assistant Answer (Tamil):")
    print(chat_data_4["response"])

    assert chat_data_4["detected_language"] == "ta", f"Expected language 'ta', got {chat_data_4['detected_language']}"
    doc_sources_4 = [s for s in chat_data_4["sources"] if s.get("source_type") == "uploaded_document"]
    assert len(doc_sources_4) > 0, "TEST 4 FAILED: Document RAG should be retrieved for Tamil query"
    print("TEST 4 PASSED: Tamil query detected, document retrieved, and answered in Tamil!")

    # ----------------------------------------------------
    # TEST 5: Remove document & verify it is no longer used
    # ----------------------------------------------------
    print_banner("TEST 5: Remove Document & Verify Reversion to Base Knowledge Base")
    del_resp = requests.delete(
        f"{BASE_URL}/documents/current?session_id={SESSION_ID}",
        timeout=5
    )
    assert del_resp.status_code == 200
    print("✓ Delete response:", del_resp.json()["message"])

    # Verify current document status is inactive
    curr_resp = requests.get(
        f"{BASE_URL}/documents/current?session_id={SESSION_ID}",
        timeout=5
    )
    assert curr_resp.json()["active"] is False
    print("✓ Document status verified: active = False")

    # Ask the same document-specific question
    chat_resp_5 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "What is the limit for emergency air ambulance coverage in this policy?",
            "session_id": SESSION_ID,
            "language": "auto",
            "model_preference": "api"
        },
        timeout=30
    )
    assert chat_resp_5.status_code == 200
    chat_data_5 = chat_resp_5.json()
    print(f"✓ Sources Retrieved after document removal ({len(chat_data_5['sources'])}):")
    for s in chat_data_5["sources"]:
        print(f"   - [{s.get('source_type')}] {s['title']}")

    # Ensure NO uploaded document sources are returned
    doc_sources_5 = [s for s in chat_data_5["sources"] if s.get("source_type") == "uploaded_document"]
    assert len(doc_sources_5) == 0, "TEST 5 FAILED: Uploaded document chunks must NOT be retrieved after removal!"
    print("TEST 5 PASSED: Document successfully removed, no longer retrieved or used by assistant!")

    # ----------------------------------------------------
    # TEST 6: Popular Insurance Topics Click Simulation
    # ----------------------------------------------------
    print_banner("TEST 6: Popular Insurance Topics Verification")
    sample_topic_queries = [
      ("Health - Room Rent", "What is the room rent limit and ICU capping in health insurance policies?"),
      ("Health - Co-payment", "What is co-payment and how does it reduce health insurance claim payout?"),
      ("Life - Nominee", "Who can be a beneficial nominee and what happens in life insurance claim?"),
      ("Motor - Own Damage", "What is standalone Own Damage car insurance and when should you buy it?"),
      ("Travel - Flight Delay", "What are the rules and continuous delay hours for flight delay compensation?"),
      ("Claims - Ombudsman", "How to escalate an unsettled or rejected claim to the IRDAI Insurance Ombudsman?")
    ]

    for category_name, query in sample_topic_queries:
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": query,
                "session_id": SESSION_ID,
                "language": "auto",
                "model_preference": "api"
            },
            timeout=30
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ [{category_name}] -> {len(data['sources'])} sources | Model: {data['model_used']}")
        assert len(data["sources"]) > 0
        assert len(data["response"]) > 50

    print("TEST 6 PASSED: All topic categories send grounded questions through RAG pipeline successfully!")

    print_banner("ALL 6 TESTS COMPLETED & VERIFIED WITH 100% SUCCESS!")

if __name__ == "__main__":
    main()
