"""
Unit Tests for BharatInsure AI Intent Router.
Verifies:
1. Greetings, Identity, and Capabilities are routed immediately without RAG/LLM.
2. Multilingual variants (Tamil, Hindi, Telugu, Kannada, Malayalam) return native text.
3. Short finance questions (e.g., 'What is UPI?', 'What is FD?') are NEVER intercepted.
4. Mixed queries (e.g., 'Hello, what is health insurance?') are NEVER intercepted.
"""

import sys
import os
import unittest

# Ensure console utf-8
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.intent.intent_router import intent_router

class TestIntentRouter(unittest.TestCase):

    def test_greetings_english(self):
        for q in ["hi", "hello", "Hey", "good morning", "good evening", "Namaste"]:
            res = intent_router.route(q, detected_language="en")
            self.assertIsNotNone(res, f"Failed on greeting: {q}")
            self.assertEqual(res["intent"], "greeting")
            self.assertTrue(res["bypassed_rag"])
            self.assertTrue(res["bypassed_llm"])
            self.assertIn("BharatInsure AI", res["response"])

    def test_greetings_multilingual(self):
        # Tamil
        res_ta = intent_router.route("வணக்கம்", detected_language="ta")
        self.assertIsNotNone(res_ta)
        self.assertIn("வணக்கம்!", res_ta["response"])

        # Hindi
        res_hi = intent_router.route("नमस्ते", detected_language="hi")
        self.assertIsNotNone(res_hi)
        self.assertIn("नमस्ते!", res_hi["response"])

        # Telugu
        res_te = intent_router.route("నమస్కారం", detected_language="te")
        self.assertIsNotNone(res_te)
        self.assertIn("నమస్కారం!", res_te["response"])

    def test_identity(self):
        for q in ["who are you", "who r u", "What is your name?", "what is bharatinsure ai", "are you an ai"]:
            res = intent_router.route(q, detected_language="en")
            self.assertIsNotNone(res, f"Failed on identity: {q}")
            self.assertEqual(res["intent"], "identity")

        # Tamil identity
        res_ta = intent_router.route("நீ யார்", detected_language="ta")
        self.assertIsNotNone(res_ta)
        self.assertEqual(res_ta["intent"], "identity")

        # Hindi identity
        res_hi = intent_router.route("आप कौन हैं", detected_language="hi")
        self.assertIsNotNone(res_hi)
        self.assertEqual(res_hi["intent"], "identity")

    def test_capabilities(self):
        for q in ["what can you do", "help", "how can you help me", "what are your features"]:
            res = intent_router.route(q, detected_language="en")
            self.assertIsNotNone(res, f"Failed on capabilities: {q}")
            self.assertEqual(res["intent"], "capabilities")

        # Hindi capabilities
        res_hi = intent_router.route("आप क्या कर सकते हैं", detected_language="hi")
        self.assertIsNotNone(res_hi)
        self.assertEqual(res_hi["intent"], "capabilities")

    def test_short_finance_questions_must_not_intercept(self):
        """CRITICAL: Short finance questions MUST bypass intent router and reach RAG!"""
        finance_queries = [
            "What is UPI?",
            "What is FD?",
            "What is RD?",
            "What is PED?",
            "What is NCB?",
            "Home loan",
            "Car insurance",
            "Health insurance",
            "Term life plan",
            "Waiting period",
            "Room rent limit",
            "Cashless hospitalisation",
            "CIBIL score",
            "SIP investment",
            "1930 helpline",
            "Tax deduction 80D",
            "காப்பீடு என்றால் என்ன?",
            "स्वास्थ्य बीमा क्या है?",
            "UPI అంటే ఏమిటి?",
            "ಹೋಮ್ ಲೋನ್"
        ]
        for q in finance_queries:
            res = intent_router.route(q, detected_language="en")
            self.assertIsNone(res, f"CRITICAL LEAK: Finance query '{q}' was incorrectly intercepted by intent router!")

    def test_mixed_queries_must_not_intercept(self):
        """Mixed queries like 'Hello, what is health insurance?' must NOT be intercepted!"""
        mixed_queries = [
            "Hi, what is health insurance?",
            "Hello, tell me about UPI autopay",
            "Good morning, what is the waiting period for diabetes?",
            "Hey, how do I file a cashless claim?",
            "Help me with my motor policy renewal"
        ]
        for q in mixed_queries:
            res = intent_router.route(q, detected_language="en")
            self.assertIsNone(res, f"CRITICAL LEAK: Mixed query '{q}' was incorrectly intercepted as a basic greeting!")

if __name__ == "__main__":
    unittest.main()
