"""
Comprehensive Finance & Fintech Knowledge Base Test Suite for BharatInsure AI.
Evaluates:
- 52 Detailed Test Questions across Payments, Banking, Loans, Credit, Investments, Security, Personal Finance
- Retrieval relevance, source correctness, latency, and precision
- Live Ollama local LLM generation on 10 representative questions
"""

import sys
import os
import time
import json
import requests

# Ensure project root is in path
sys.path.insert(0, os.path.abspath("."))
sys.stdout.reconfigure(encoding="utf-8")

from backend.services.rag.retriever import rag_retriever
from backend.services.llm.local_model_service import local_llm_service

BASE_URL = "http://127.0.0.1:8000"

# 52 Comprehensive Test Queries Covering All Finance & Fintech Pillars
TEST_QUERIES = [
    # --- Category A: Digital Payments (1-8) ---
    {
        "id": "Q01",
        "category": "Digital Payments",
        "query": "What is UPI and how does Virtual Payment Address VPA work?",
        "expected_ids": ["fintech-01"],
        "type": "direct_factual"
    },
    {
        "id": "Q02",
        "category": "Digital Payments",
        "query": "Do I need to enter my UPI PIN to receive money from a buyer?",
        "expected_ids": ["fintech-02"],
        "type": "direct_factual"
    },
    {
        "id": "Q03",
        "category": "Digital Payments",
        "query": "What is the difference between IMPS, NEFT, and RTGS transfers?",
        "expected_ids": ["fintech-03"],
        "type": "comparison"
    },
    {
        "id": "Q04",
        "category": "Digital Payments",
        "query": "What is the minimum transaction limit for RTGS fund transfer?",
        "expected_ids": ["fintech-03"],
        "type": "regulatory_limit"
    },
    {
        "id": "Q05",
        "category": "Digital Payments",
        "query": "What is a Prepaid Payment Instrument PPI or digital wallet?",
        "expected_ids": ["fintech-04"],
        "type": "direct_factual"
    },
    {
        "id": "Q06",
        "category": "Digital Payments",
        "query": "My money was debited but the UPI payment failed. What is the RBI T+1 refund rule?",
        "expected_ids": ["fintech-05"],
        "type": "dispute_tat"
    },
    {
        "id": "Q07",
        "category": "Digital Payments",
        "query": "What compensation am I entitled to if a failed transaction is not refunded in time?",
        "expected_ids": ["fintech-05"],
        "type": "regulatory_compensation"
    },
    {
        "id": "Q08",
        "category": "Digital Payments",
        "query": "How to resolve a duplicate debit and request a chargeback from the bank?",
        "expected_ids": ["fintech-06"],
        "type": "dispute_resolution"
    },

    # --- Category B: Banking (9-16) ---
    {
        "id": "Q09",
        "category": "Banking",
        "query": "What is the difference between savings account and current account?",
        "expected_ids": ["bank-01"],
        "type": "comparison"
    },
    {
        "id": "Q10",
        "category": "Banking",
        "query": "How does Fixed Deposit FD differ from Recurring Deposit RD?",
        "expected_ids": ["bank-02"],
        "type": "acronym_comparison"
    },
    {
        "id": "Q11",
        "category": "Banking",
        "query": "What is the DICGC deposit insurance limit for bank deposits?",
        "expected_ids": ["bank-02"],
        "type": "regulatory_safety"
    },
    {
        "id": "Q12",
        "category": "Banking",
        "query": "Can a bank account balance turn negative due to minimum balance penalty charges?",
        "expected_ids": ["bank-03"],
        "type": "rbi_rule"
    },
    {
        "id": "Q13",
        "category": "Banking",
        "query": "What is a zero-balance BSBDA Basic Savings Bank Deposit Account?",
        "expected_ids": ["bank-03"],
        "type": "acronym_factual"
    },
    {
        "id": "Q14",
        "category": "Banking",
        "query": "What is the legal role of a nominee in a bank savings account?",
        "expected_ids": ["bank-04"],
        "type": "legal_nomination"
    },
    {
        "id": "Q15",
        "category": "Banking",
        "query": "What happens when a bank account becomes dormant or inoperative after 2 years?",
        "expected_ids": ["bank-05"],
        "type": "kyc_status"
    },
    {
        "id": "Q16",
        "category": "Banking",
        "query": "How to file a complaint with the RBI Integrated Ombudsman on CMS portal?",
        "expected_ids": ["bank-06"],
        "type": "grievance_ombudsman"
    },

    # --- Category C: Loans and EMI (17-23) ---
    {
        "id": "Q17",
        "category": "Loans & EMI",
        "query": "What is the difference between secured and unsecured loans?",
        "expected_ids": ["loan-01"],
        "type": "comparison"
    },
    {
        "id": "Q18",
        "category": "Loans & EMI",
        "query": "How is EMI calculated and what is an amortisation schedule?",
        "expected_ids": ["loan-02"],
        "type": "amortisation"
    },
    {
        "id": "Q19",
        "category": "Loans & EMI",
        "query": "Why is a reducing balance interest rate cheaper than a flat interest rate?",
        "expected_ids": ["loan-02"],
        "type": "math_concept"
    },
    {
        "id": "Q20",
        "category": "Loans & EMI",
        "query": "What is a moratorium period in education loans?",
        "expected_ids": ["loan-03"],
        "type": "product_feature"
    },
    {
        "id": "Q21",
        "category": "Loans & EMI",
        "query": "Can banks levy foreclosure penalty on floating rate home loans?",
        "expected_ids": ["loan-04"],
        "type": "rbi_prohibition"
    },
    {
        "id": "Q22",
        "category": "Loans & EMI",
        "query": "What are the RBI guidelines on penal charges in loan accounts?",
        "expected_ids": ["loan-05"],
        "type": "fair_lending"
    },
    {
        "id": "Q23",
        "category": "Loans & EMI",
        "query": "How do predatory instant loan apps trap borrowers and what are digital lending guidelines?",
        "expected_ids": ["loan-06"],
        "type": "scam_protection"
    },

    # --- Category D: Credit and Cards (24-29) ---
    {
        "id": "Q24",
        "category": "Credit & Cards",
        "query": "What is the difference between credit score and credit rating?",
        "expected_ids": ["cred-01"],
        "type": "acronym_disambiguation"
    },
    {
        "id": "Q25",
        "category": "Credit & Cards",
        "query": "What is Credit Utilisation Ratio CUR and how does it affect CIBIL score?",
        "expected_ids": ["cred-02"],
        "type": "score_factor"
    },
    {
        "id": "Q26",
        "category": "Credit & Cards",
        "query": "How does credit card billing cycle and interest-free grace period work?",
        "expected_ids": ["cred-03"],
        "type": "card_operations"
    },
    {
        "id": "Q27",
        "category": "Credit & Cards",
        "query": "What is the Minimum Amount Due MAD trap on credit cards?",
        "expected_ids": ["cred-04"],
        "type": "financial_trap"
    },
    {
        "id": "Q28",
        "category": "Credit & Cards",
        "query": "What is the customer liability for unauthorized card fraud reported within 3 days?",
        "expected_ids": ["cred-05"],
        "type": "zero_liability"
    },
    {
        "id": "Q29",
        "category": "Credit & Cards",
        "query": "How to dispute an erroneous loan on my CIBIL credit report within 30 days?",
        "expected_ids": ["cred-06"],
        "type": "dispute_bureau"
    },

    # --- Category E: Savings and Investments (30-36) ---
    {
        "id": "Q30",
        "category": "Savings & Investments",
        "query": "What is Net Asset Value NAV and Total Expense Ratio TER in mutual funds?",
        "expected_ids": ["inv-01"],
        "type": "acronym_factual"
    },
    {
        "id": "Q31",
        "category": "Savings & Investments",
        "query": "How does rupee cost averaging work in Systematic Investment Plan SIP?",
        "expected_ids": ["inv-02"],
        "type": "investment_method"
    },
    {
        "id": "Q32",
        "category": "Savings & Investments",
        "query": "What is the difference between equity funds, debt funds, and index funds?",
        "expected_ids": ["inv-03"],
        "type": "scheme_categorization"
    },
    {
        "id": "Q33",
        "category": "Savings & Investments",
        "query": "What are Sovereign Gold Bonds SGB and how to buy G-Sec on RBI Retail Direct?",
        "expected_ids": ["inv-04"],
        "type": "gsec_gold"
    },
    {
        "id": "Q34",
        "category": "Savings & Investments",
        "query": "What is the SEBI Riskometer and why does asset diversification matter?",
        "expected_ids": ["inv-05"],
        "type": "risk_management"
    },
    {
        "id": "Q35",
        "category": "Savings & Investments",
        "query": "How does inflation affect nominal versus real investment returns?",
        "expected_ids": ["inv-06"],
        "type": "economic_math"
    },
    {
        "id": "Q36",
        "category": "Savings & Investments",
        "query": "What is the BUDS Act 2019 and how to identify Ponzi schemes with guaranteed returns?",
        "expected_ids": ["inv-07"],
        "type": "scam_law"
    },

    # --- Category F: Personal Finance (37-41) ---
    {
        "id": "Q37",
        "category": "Personal Finance",
        "query": "How does the 50/30/20 budgeting rule work for personal salary allocation?",
        "expected_ids": ["pf-01"],
        "type": "budget_framework"
    },
    {
        "id": "Q38",
        "category": "Personal Finance",
        "query": "How much money should I keep in an emergency fund and where to park it?",
        "expected_ids": ["pf-02"],
        "type": "emergency_planning"
    },
    {
        "id": "Q39",
        "category": "Personal Finance",
        "query": "What is the 30-day rule to distinguish needs from wants and curb lifestyle inflation?",
        "expected_ids": ["pf-03"],
        "type": "spending_habit"
    },
    {
        "id": "Q40",
        "category": "Personal Finance",
        "query": "What is the difference between Debt Avalanche and Debt Snowball repayment strategies?",
        "expected_ids": ["pf-04"],
        "type": "debt_strategy"
    },
    {
        "id": "Q41",
        "category": "Personal Finance",
        "query": "Why should you never mix insurance with investment by buying endowment policies?",
        "expected_ids": ["pf-06"],
        "type": "mistake_warning"
    },

    # --- Category G: Digital Security & Fraud (42-46) ---
    {
        "id": "Q42",
        "category": "Digital Security & Fraud",
        "query": "How do phishing scams and fake search engine customer care numbers operate?",
        "expected_ids": ["sec-01"],
        "type": "phishing_fraud"
    },
    {
        "id": "Q43",
        "category": "Digital Security & Fraud",
        "query": "Can scanning a QR code or approving a collect request deduct money from my account?",
        "expected_ids": ["sec-02"],
        "type": "qr_safety"
    },
    {
        "id": "Q44",
        "category": "Digital Security & Fraud",
        "query": "What is SIM swap fraud and why is OTP security critical?",
        "expected_ids": ["sec-03"],
        "type": "credential_fraud"
    },
    {
        "id": "Q45",
        "category": "Digital Security & Fraud",
        "query": "Why do fraudsters ask victims to install AnyDesk or TeamViewer QuickSupport?",
        "expected_ids": ["sec-04"],
        "type": "remote_access"
    },
    {
        "id": "Q46",
        "category": "Digital Security & Fraud",
        "query": "What is the cybercrime helpline 1930 and what to do in the Golden Hour after fraud?",
        "expected_ids": ["sec-06"],
        "type": "emergency_reporting"
    },

    # --- Category H: Insurance-Fintech Connections (47-49) ---
    {
        "id": "Q47",
        "category": "Insurance & Fintech",
        "query": "Can I pay insurance policy premiums using UPI AutoPay recurring mandate?",
        "expected_ids": ["insfin-01"],
        "type": "ins_fintech"
    },
    {
        "id": "Q48",
        "category": "Insurance & Fintech",
        "query": "What is an Electronic Insurance Account eIA and what are approved Insurance Repositories?",
        "expected_ids": ["insfin-02"],
        "type": "eia_repository"
    },
    {
        "id": "Q49",
        "category": "Insurance & Fintech",
        "query": "How does insurance e-KYC work and is a DigiLocker policy document legally valid?",
        "expected_ids": ["insfin-03"],
        "type": "digilocker_kyc"
    },

    # --- Category I: Indic Multilingual Queries (50-51) ---
    {
        "id": "Q50",
        "category": "Multilingual Tamil",
        "query": "பிக்சட் டெபாசிட் (FD) மற்றும் தொடர் வைப்பு நிதி (RD) வித்தியாசம் என்ன?",
        "expected_ids": ["bank-02"],
        "type": "indic_tamil"
    },
    {
        "id": "Q51",
        "category": "Multilingual Hindi",
        "query": "क्रेडिट कार्ड का मिनिमम ड्यू (MAD) चुकाने का क्या नुकसान है?",
        "expected_ids": ["cred-04"],
        "type": "indic_hindi"
    },

    # --- Category J: Out-of-Scope Control (52) ---
    {
        "id": "Q52",
        "category": "Out of Scope",
        "query": "Who won the cricket world cup in 1983 and what was the final score?",
        "expected_ids": [],
        "type": "out_of_scope"
    }
]

def run_retrieval_suite():
    print("=" * 80)
    print("PHASE 6: 52-QUERY COMPREHENSIVE RETRIEVAL BENCHMARK")
    print("=" * 80)

    passed = 0
    total = len(TEST_QUERIES)
    latencies = []

    for item in TEST_QUERIES:
        q_id = item["id"]
        q_text = item["query"]
        expected = item["expected_ids"]

        t0 = time.time()
        sources = rag_retriever.retrieve(query=q_text, top_k=3)
        elapsed_ms = round((time.time() - t0) * 1000, 2)
        latencies.append(elapsed_ms)

        retrieved_ids = [s.id for s in sources]

        # Verification logic
        if not expected:
            # Out of scope query should return 0 sources
            is_correct = len(sources) == 0
        else:
            # At least one expected ID should be in retrieved sources
            is_correct = any(exp in retrieved_ids for exp in expected)

        if is_correct:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"

        top_info = f"Top: {retrieved_ids[0]} ({sources[0].relevance_score})" if sources else "Top: None"
        print(f"[{status}] {q_id} ({item['category']}): {elapsed_ms}ms | Expected: {expected} | Retrieved: {retrieved_ids} | {top_info}")

    avg_latency = round(sum(latencies) / len(latencies), 2)
    accuracy = round((passed / total) * 100, 1)

    print("\n" + "=" * 80)
    print(f"RETRIEVAL BENCHMARK SUMMARY: {passed}/{total} Passed ({accuracy}%)")
    print(f"Average Retrieval Latency: {avg_latency} ms | Total Chunks Indexed: {len(rag_retriever.documents)}")
    print("=" * 80)
    assert passed >= 48, f"Too many retrieval failures: {passed}/{total}"
    return accuracy, avg_latency

def run_live_llm_generation_sample():
    print("\n" + "=" * 80)
    print("LIVE OLLAMA GENERATION ON 10 REPRESENTATIVE FINANCE QUESTIONS")
    print("=" * 80)

    sample_questions = [
        ("Digital Payments - UPI PIN", "Do I need to enter my UPI PIN to receive money from a buyer?"),
        ("Banking - FD vs RD", "What is the difference between Fixed Deposit FD and Recurring Deposit RD?"),
        ("Banking - Negative Balance", "Can a savings account balance become negative due to minimum balance penalty?"),
        ("Loans - Flat vs Reducing", "Why is a reducing balance interest rate cheaper than a flat interest rate on a loan?"),
        ("Loans - Foreclosure", "Can banks charge foreclosure penalty on floating rate home loans?"),
        ("Credit - MAD Trap", "What happens if I only pay the Minimum Amount Due MAD on my credit card?"),
        ("Investments - SGB", "What is Sovereign Gold Bond SGB and are the capital gains tax-free?"),
        ("Personal Finance - 50/30/20", "Explain the 50/30/20 budgeting rule in simple words."),
        ("Digital Security - QR Scam", "Can scanning a QR code deduct money from my account?"),
        ("Insurance-Fintech - eIA", "What is an Electronic Insurance Account eIA and what are its benefits?")
    ]

    results = []
    for label, q_text in sample_questions:
        print(f"\n--- Testing: {label} ---")
        t0 = time.time()
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": q_text,
                "session_id": f"eval-sample-{int(time.time())}",
                "language": "en",
                "model_preference": "local_small"
            },
            timeout=60
        )
        wall_time = round((time.time() - t0) * 1000, 1)
        data = resp.json()
        model_used = data.get("model_used")
        backend_lat = data.get("latency_ms")
        sources = data.get("sources", [])
        src_ids = [s.get("id") for s in sources]
        answer = data.get("response", "").strip()

        print(f"Wall Latency: {wall_time}ms | Backend Latency: {backend_lat}ms | Model: {model_used}")
        print(f"Sources ({len(sources)}): {src_ids}")
        print(f"Answer Sample:\n{answer[:220]}...\n")

        results.append({
            "label": label,
            "question": q_text,
            "wall_latency_ms": wall_time,
            "backend_latency_ms": backend_lat,
            "sources": src_ids,
            "answer_preview": answer[:180]
        })

    return results

def main():
    acc, avg_lat = run_retrieval_suite()
    sample_gen_results = run_live_llm_generation_sample()

    output_summary = {
        "retrieval_accuracy_percent": acc,
        "average_retrieval_latency_ms": avg_lat,
        "total_test_queries": len(TEST_QUERIES),
        "total_indexed_documents": len(rag_retriever.documents),
        "sample_generation_results": sample_gen_results
    }

    with open("tests/finance_evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(output_summary, f, indent=2, ensure_ascii=False)
    print("\nSaved full evaluation results to tests/finance_evaluation_results.json")

if __name__ == "__main__":
    main()
