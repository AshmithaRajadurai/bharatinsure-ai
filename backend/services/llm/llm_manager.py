"""
Multilingual LLM Service Manager for BharatInsure AI.
Supports:
1. API Baseline: Google Gemini / OpenAI / Groq
2. Local Small Model: Qwen2.5-3B-Instruct / Grounded Indic Neural Engine
Supports Active Uploaded Document grounding + IRDAI Base Knowledge Base.
"""

import os
import time
import re
from typing import Dict, Any, List, Optional
from backend.models.schemas import RAGSource
from backend.services.language.detector import LanguageDetector
from backend.services.llm.local_model_service import local_llm_service

# Disclaimer text
DISCLAIMER_TEXT = "This AI assistant provides general insurance information and does not replace professional financial, legal, or insurance advice."

OUT_OF_SCOPE_TRANSLATIONS = {
    "en": "I couldn't find relevant insurance or fintech records for this query in the knowledge base. BharatInsure AI is specialized in Indian insurance policies, digital payments, banking, loans, investments, and personal finance.",
    "hi": "ज्ञानकोष में इस प्रश्न के लिए कोई प्रासंगिक बीमा या फिनटेक रिकॉर्ड नहीं मिला। भारत इंश्योरेंस एआई विशेष रूप से भारतीय बीमा, डिजिटल भुगतान, बैंकिंग, ऋण और व्यक्तिगत वित्त पर सहायता प्रदान करता है।",
    "ta": "இந்தக் கேள்விக்கான நேரடி காப்பீட்டு அல்லது நிதி ஆவணங்கள் அறிவுத்தளத்தில் கிடைக்கவில்லை. பாரத் இன்ஷூரன்ஸ் AI பிரத்யேகமாக இந்திய காப்பீடு, டிஜிட்டல் பேமெண்ட்கள், வங்கி, கடன்கள் மற்றும் தனிநபர் நிதியில் வழிகாட்டுகிறது.",
    "te": "నాలెడ్జ్ బేస్‌లో ఈ ప్రశ్నకు సంబంధించిన సంబంధిత బీమా లేదా ఫిన్‌టెక్ రికార్డులు కనుగొనబడలేదు. భారత్ ఇన్సూరెన్స్ AI ప్రత్యేకంగా భారతీయ బీమా, డిజిటల్ చెల్లింపులు, బ్యాంకింగ్ మరియు రుణాలపై మార్गదర్శకత్వం అందిస్తుంది.",
    "kn": "ಜ್ಞಾನಕೋಶದಲ್ಲಿ ಈ ಪ್ರಶ್ನೆಗೆ ಸಂಬಂಧಿಸಿದ ಯಾವುದೇ ಸೂಕ್ತ ವಿಮಾ ಅಥವಾ ಫಿನ್‌ಟೆಕ್ ದಾಖಲೆಗಳು ಕಂಡುಬಂದಿಲ್ಲ. ಭಾರತ್ ಇನ್ಶೂರೆನ್ಸ್ AI ಭಾರತೀಯ ವಿಮೆ, ಡಿಜಿಟಲ್ ಪಾವತಿಗಳು, ಬ್ಯಾಂಕಿಂಗ್ ಮತ್ತು ಸಾಲಗಳಲ್ಲಿ ನೆರವು ನೀಡುತ್ತದೆ.",
    "ml": "നോളജ് ബേസിൽ ഈ ചോദ്യത്തിന് പ്രസക്തമായ ഇൻഷുറൻസ് അല്ലെങ്കിൽ ഫിൻടെക് വിവരങ്ങൾ കണ്ടെത്താനായില്ല. ഭാരത് ഇൻഷുറൻസ് AI ഇന്ത്യൻ ഇൻഷുറൻസ്, ഡിജിറ്റൽ പേയ്‌മെന്റുകൾ, ബാങ്കിംഗ്, വായ്പകൾ എന്നിവയിലാണ് മാർഗ്ഗനിർദ്ദേശം നൽകുന്നത്."
}

NOT_FOUND_IN_DOC_TRANSLATIONS = {
    "en": "I couldn't find this information in the uploaded document.",
    "hi": "अपलोड किए गए दस्तावेज़ में यह जानकारी नहीं मिली।",
    "ta": "பதிவேற்றப்பட்ட ஆவணத்தில் இந்த தகவல் கிடைக்கவில்லை.",
    "te": "అప్‌లోడ్ చేసిన పత్రంలో ఈ సమాచారం కనుగొనబడలేదు.",
    "kn": "ಅಪ್‌ಲೋಡ್ ಮಾಡಿದ ದಾಖಲೆಯಲ್ಲಿ ಈ ಮಾಹಿತಿ ಕಂಡುಬಂದಿಲ್ಲ.",
    "ml": "അപ്‌ലോഡ് ചെയ്ത രേഖയിൽ ഈ വിവരം കണ്ടെത്താനായില്ല."
}

INDIC_RESPONSES = {
    "ta": {
        "greeting": "வணக்கம்! நான் பாரத் இன்ஷூரன்ஸ் AI (BharatInsure AI). மருத்துவ காப்பீடு, ஆயுள் காப்பீடு, வாகன காப்பீடு மற்றும் கிளைம் செயல்முறைகள் பற்றி உங்களுக்கு எவ்வாறு உதவ முடியும்?",
        "disclaimer": "குறிப்பு: இது பொதுவான தகவல் மட்டுமே. தொழில்முறை நிதி அல்லது காப்பீட்டு ஆலோசனையல்ல.",
        "health_intro": "மருத்துவ காப்பீடு (Health Insurance) என்பது நோய் அல்லது விபத்தினால் ஏற்படும் மருத்துவமனை சிகிச்சை செலவுகளுக்கு நிதி பாதுகாப்பு அளிக்கிறது. இதில் கேஷ்லெஸ் (Cashless) மற்றும் ரீஇம்பர்ஸ்மென்ட் (Reimbursement) முறைகள் உள்ளன.",
        "waiting_period": "மருத்துவ காப்பீட்டில் பொதுவான காத்திருப்பு காலம் (Waiting Period): ஆரம்ப காத்திருப்பு காலம் 30 நாட்கள் (விபத்து தவிர). ஏற்கனவே உள்ள நோய்களுக்கு (PED) IRDAI விதிகளின்படி 24 முதல் 36 மாதங்கள். குறிப்பிட்ட அறுவை சிகிச்சைகளுக்கு 1 முதல் 2 ஆண்டுகள்.",
        "claims": "காப்பீட்டு உரிமைகோரல் (Claim): நெட்வொர்க் மருத்துவமனைகளில் கேஷ்லெஸ் முறை மூலம் சிகிச்சை பெறலாம். நெட்வொர்க் அல்லாத மருத்துவமனைகளில் பில்கள் செலுத்திய பின் 15-30 நாட்களுக்குள் ஆவணங்களைச் சமர்ப்பித்து ரீஇம்பர்ஸ்மென்ட் பெறலாம்.",
        "motor": "இந்தியாவில் மோட்டார் வாகனச் சட்டப்படி மூன்றாம் தரப்பு காப்பீடு (Third-Party Insurance) கட்டாயம். சொந்த வாகன சேதத்திற்கும் பாதுகாப்பு பெற விரிவான (Comprehensive) மற்றும் ஜீரோ டெப்ரிசியேஷன் (Zero Dep) காப்பீடு சிறந்தது.",
        "life": "ஆயுள் காப்பீடு (Life Insurance) குடும்பத்தின் நிதிப் பாதுகாப்பை உறுதி செய்கிறது. டேர்ம் பிளான் (Term Plan) குறைந்த பிரீமியத்தில் அதிக கவரேஜ் வழங்குகிறது. விபத்து மற்றும் தீவிர நோய் ரைடர்கள் (Riders) கூடுதல் பலன் அளிக்கின்றன."
    },
    "hi": {
        "greeting": "नमस्ते! मैं भारत इंश्योरेंस एआई (BharatInsure AI) हूँ। स्वास्थ्य बीमा, जीवन बीमा, मोटर बीमा और क्लेम प्रक्रिया के बारे में मैं आपकी क्या सहायता कर सकता हूँ?",
        "disclaimer": "नोट: यह केवल सामान्य बीमा जानकारी है और पेशेवर वित्तीय सलाह का विकल्प नहीं है।",
        "health_intro": "स्वास्थ्य बीमा (Health Insurance) बीमारी या दुर्घटना के दौरान अस्पताल के खर्चों से वित्तीय सुरक्षा प्रदान करता है। इसमें कैशलेस (Cashless) और रीइंबर्समेंट (Reimbursement) दोनों सुविधाएं उपलब्ध हैं।",
        "waiting_period": "स्वास्थ्य बीमा में प्रतीक्षा अवधि (Waiting Period): शुरुआत के 30 दिन आपातकालीन दुर्घटनाओं को छोड़कर कोई सामान्य बीमारी कवर नहीं होती। पहले से मौजूद बीमारियों (PED) के लिए IRDAI के अनुसार 24 से 36 महीने की प्रतीक्षा अवधि होती है।",
        "claims": "बीमा क्लेम (Claim Process): नेटवर्क अस्पतालों में TPA डेस्क के जरिए कैशलेस क्लेम उपलब्ध होता है। गैर-नेटवर्क अस्पतालों में डिस्चार्ज के बाद 15 से 30 दिनों के भीतर बिल जमा करके रीइंबर्समेंट प्राप्त किया जा सकता है।",
        "motor": "मोटर बीमा: भारत में थर्ड-पार्टी बीमा कानूनी रूप से अनिवार्य है। वाहन की पूरी सुरक्षा के लिए कॉम्प्रीहेंसिव बीमा और जीरो डेप्रिसिएशन (Zero Dep) एड-ऑन सबसे बेहतर विकल्प हैं।",
        "life": "जीवन बीमा (Life Insurance): परिवार के सुरक्षित भविष्य के लिए टर्म इंश्योरेंस सबसे किफायती और सुरक्षित विकल्प है, जिसमें नॉमिनी को सम एश्योर्ड का भुगतान मिलता है।"
    },
    "te": {
        "greeting": "నమస్కారం! నేను భారత్ ఇన్సూరెన్స్ AI. ఆరోగ్య బీమా, జీవిత బీమా, మోటార్ బీమా మరియు క్లెయిమ్ ప్రక్రియలపై మీకు సహాయం చేయడానికి సిద్ధంగా ఉన్నాను.",
        "disclaimer": "గమనిక: ఇది సాధారణ సమాచారం మాత్రమే. వృత్తిపరమైన ఆర్థిక సలహా కాదు.",
        "health_intro": "ఆరోగ్య బీమా (Health Insurance) ఆసుపత్రి ఖర్చులు మరియు చికిత్సలకు రక్షణ కల్పిస్తుంది. ఇందులో క్యాష్‌లెస్ మరియు రీయింబర్స్‌మెంట్ సౌకర్యాలు ఉన్నాయి.",
        "waiting_period": "ఆరోగ్య బీమాలో వేచి ఉండే కాలం (Waiting Period): ప్రారంభంలో 30 రోజులు. ముందున్న వ్యాధులకు (PED) 24 నుండి 36 నెలల వరకు వేచి ఉండే సమయం ఉంటుంది.",
        "claims": "క్లెయిమ్ ప్రక్రియ: నెట్‌వర్క్ ఆసుపత్రులలో ముందస్తు అనుమతితో క్యాష్‌లెస్ చికిత్స పొందవచ్చు. లేదా బిల్లులు సమర్పించి రీయింబర్స్‌మెంట్ పొందవచ్చు.",
        "motor": "మోటార్ బీమా: థర్డ్-పార్టీ ఇన్సూరెన్స్ చట్టబద్ధంగా తప్పనిసరి. పూర్తి వాహన రక్షణ కోసం కాంప్రహెన్సివ్ మరియు జీరో డెప్రిసియేషన్ ఎంచుకోవచ్చు.",
        "life": "జీవిత బీమా (Life Insurance): కుటుంబ ఆర్థిక భద్రత కోసం టర్మ్ ఇన్సూరెన్స్ అధిక కవరేజీని తక్కువ ప్రీమియంతో అందిస్తుంది."
    },
    "kn": {
        "greeting": "ನಮಸ್ಕಾರ! ನಾನು ಭಾರತ್ ಇನ್ಶೂರೆನ್ಸ್ AI. ಆರೋಗ್ಯ ವಿಮೆ, ಜೀವ ವಿಮೆ, ವಾಹನ ವಿಮೆ ಮತ್ತು ಕ್ಲೈಮ್ ಪ್ರಕ್ರಿಯೆಗಳ ಬಗ್ಗೆ ನಿಮಗೆ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ.",
        "disclaimer": "ಗಮನಿಸಿ: ಇದು ಸಾಮಾನ್ಯ ವಿಮಾ ಮಾಹಿತಿ ಮಾತ್ರ.",
        "health_intro": "ಆರೋಗ್ಯ ವಿಮೆ (Health Insurance) ವೈದ್ಯಕೀಯ ಮತ್ತು ಆಸ್ಪತ್ರೆಯ ವೆಚ್ಚಗಳಿಂದ ಹಣಕಾಸಿನ ರಕ್ಷಣೆ ನೀಡುತ್ತದೆ. ಕ್ಯಾಶ್‌ಲೆಸ್ ಮತ್ತು ಮರುಪಾವತಿ ಆಯ್ಕೆಗಳು ಲಭ್ಯವಿದೆ.",
        "waiting_period": "ಕಾಯುವ ಅವಧಿ (Waiting Period): ಆರಂಭಿಕ 30 ದಿನಗಳು. ಮೊದಲೇ ಇರುವ ರೋಗಗಳಿಗೆ (PED) 24 ರಿಂದ 36 ತಿಂಗಳ ಕಾಯುವಿಕೆ ಇರುತ್ತದೆ.",
        "claims": "ಕ್ಲೈಮ್ ಪ್ರಕ್ರಿಯೆ: ನೆಟ್‌ವರ್ಕ್ ಆಸ್ಪತ್ರೆಗಳಲ್ಲಿ ಕ್ಯಾಶ್‌ಲೆಸ್ ಸೌಲಭ್ಯ ಲಭ್ಯವಿದೆ. ಇತರ ಆಸ್ಪತ್ರೆಗಳಲ್ಲಿ ಬಿಲ್ ಸಲ್ಲಿಸಿ ಮರುಪಾವತಿ ಪಡೆಯಬಹುದು.",
        "motor": "ವಾಹನ ವಿಮೆ: ಥರ್ಡ್-ಪಾರ್ಟಿ ವಿಮೆ ಕಡ್ಡಾಯವಾಗಿದೆ. ಪೂರ್ಣ ರಕ್ಷಣೆಗಾಗಿ ಕಾಂಪ್ರಹೆನ್ಸಿವ್ ಮತ್ತು ಜೀರೋ ಡಿಪ್ರಿಸಿಯೇಶನ್ ವಿಮೆ ಸೂಕ್ತವಾಗಿದೆ.",
        "life": "ಜೀವ ವಿಮೆ: ಕುಟುಂಬದ ಭವಿಷ್ಯದ ಆರ್ಥಿಕ ಭದ್ರತೆಗಾಗಿ ಟರ್ಮ್ ಇನ್ಶೂರೆನ್ಸ್ ಅತ್ಯುತ್ತಮ ಆಯ್ಕೆಯಾಗಿದೆ."
    },
    "ml": {
        "greeting": "നമസ്കാരം! ഞാൻ ഭാരത് ഇൻഷുറൻസ് AI. ആരോഗ്യ ഇൻഷുറൻസ്, ലൈഫ് ഇൻഷുറൻസ്, വാഹന ഇൻഷുറൻസ്, ക്ലെയിം പ്രക്രിയകൾ എന്നിവയിൽ സഹായിക്കാൻ ഞാൻ ഇവിടെയുണ്ട്.",
        "disclaimer": "ശ്രദ്ധിക്കുക: ഇത് പൊതുവായ വിവരങ്ങൾ മാത്രമാണ്. സാമ്പത്തിക ഉപദേശമല്ല.",
        "health_intro": "ആരോഗ്യ ഇൻഷുറൻസ് (Health Insurance) അപ്രതീക്ഷിത മെഡിക്കൽ ചെലവുകളിൽ നിന്ന് സാമ്പത്തിക സംരക്ഷണം നൽകുന്നു. ക്യാഷ്‌ലെസ്സ്, റീഇംബേഴ്സ്മെന്റ് സൗകര്യങ്ങൾ ലഭ്യമാണ്.",
        "waiting_period": "കാത്തിരിപ്പ് കാലാവധി (Waiting Period): പ്രാരംഭ 30 ദിവസങ്ങൾ. മുൻപുണ്ടായിരുന്ന രോഗങ്ങൾക്ക് (PED) 24 മുതൽ 36 മാസം വരെയാണ് കാലാവധി.",
        "claims": "ക്ലെയിം രീതി: നെറ്റ്‌വർക്ക് ആശുപത്രികളിൽ ക്യാഷ്‌ലെസ്സ് ചികിത്സ ലഭ്യമാണ്. അല്ലാത്തവയിൽ ബില്ലുകൾ സമർപ്പിച്ച് റീഇംബേഴ്സ്മെന്റ് നേടാം.",
        "motor": "വാഹന ഇൻഷുറൻസ്: തേർഡ് പാർട്ടി ഇൻഷുറൻസ് നിയമപരമായി നിർബന്ധമാണ്. കൂടുതൽ സുരക്ഷിതത്വത്തിന് സമഗ്ര പോളിസിയും സീറോ ഡിപ്രീസിയേഷനും തിരഞ്ഞെടുക്കാം.",
        "life": "ലൈഫ് ഇൻഷുറൻസ്: കുടുംബത്തിന്റെ സാമ്പത്തിക ഭദ്രത ഉറപ്പാക്കാൻ ടേം ഇൻഷുറൻസ് ഏറ്റവും അനുയോജ്യമാണ്."
    },
    "en": {
        "greeting": "Hello! I am BharatInsure AI – your Multilingual Fintech & Insurance Assistant. How may I help you with Health, Life, Motor, Travel Insurance, or Claims today?",
        "disclaimer": DISCLAIMER_TEXT,
        "health_intro": "Health insurance covers hospitalization, day-care procedures, and medical treatments through Cashless network hospital settlement or Reimbursement.",
        "waiting_period": "Standard health insurance waiting periods in India: Initial waiting period of 30 days (except accidental injury). Pre-existing conditions (PED) waiting period is typically 24-36 months per IRDAI norms. Specific diseases (cataract, hernia, joint replacement) carry 1-2 years.",
        "claims": "Claim settlement is available through two channels: (1) Cashless Settlement at network hospitals with prior pre-authorization, or (2) Reimbursement where bills and discharge summaries are submitted within 15-30 days.",
        "motor": "Motor insurance under the Motor Vehicles Act 1988 mandates Third-Party Liability cover. Comprehensive insurance adds Own Damage protection, with Zero Depreciation add-on being highly recommended.",
        "life": "Term life insurance offers high sum assured protection at affordable premiums. Riders such as Accidental Death and Critical Illness provide enhanced coverage."
    }
}

class LLMManager:
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")

    def _call_gemini_rest(self, prompt: str) -> Optional[str]:
        """Direct REST call to Gemini API."""
        if not self.gemini_api_key:
            return None
        import requests
        models_to_try = ["gemini-1.5-flash-latest", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"]
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}
        }
        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_api_key}"
            try:
                resp = requests.post(url, json=payload, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception:
                pass
        return None

    def _call_openai_compatible_rest(self, prompt: str, api_key: str, base_url: str, model_name: str) -> Optional[str]:
        """Direct REST call to OpenAI or Groq API."""
        import requests
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 600
        }
        try:
            resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[LLM Manager] OpenAI REST error: {e}")
        return None

    @staticmethod
    def _format_document_citations(doc_sources: List[RAGSource]) -> str:
        """
        Build exact page-level citations according to Requirement 4:
        - Source: Page X, "Section Name"
        - Supporting clause: "Exact excerpt"
        Only shows page numbers that were preserved during extraction.
        """
        if not doc_sources:
            return ""
        top_doc = doc_sources[0]
        page_str = f"Page {top_doc.page}" if top_doc.page else "Document"
        section_name = top_doc.section_heading or "Policy Terms"
        snippet_clean = top_doc.snippet.strip().replace("\n", " ")
        if len(snippet_clean) > 160:
            excerpt = snippet_clean[:160].rsplit(" ", 1)[0] + "..."
        else:
            excerpt = snippet_clean

        lines = [
            f"\n**Source:** {page_str}, \"{section_name}\"",
            f"**Supporting clause:** \"{excerpt}\""
        ]

        # Multi-clause citation if second doc chunk is on another page or different clause
        if len(doc_sources) > 1 and (doc_sources[1].page != top_doc.page or doc_sources[1].section_heading != top_doc.section_heading):
            second = doc_sources[1]
            p2 = f"Page {second.page}" if second.page else "Document"
            s2 = second.section_heading or "Conditions"
            snip2 = second.snippet.strip().replace("\n", " ")
            ex2 = snip2[:130].rsplit(" ", 1)[0] + "..." if len(snip2) > 130 else snip2
            lines.append(f"**Additional Source:** {p2}, \"{s2}\"\n**Supporting clause:** \"{ex2}\"")

        return "\n".join(lines)

    def generate_response(
        self,
        query: str,
        detected_language: str,
        sources: List[RAGSource],
        conversation_history_text: str,
        model_preference: str = "api",
        active_document: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate answer using RAG context in the detected Indian language.
        When active_document is present, grounds answer in the uploaded document.
        """
        start_time = time.time()
        lang_info = LanguageDetector.get_language_info(detected_language)
        lang_name = lang_info["name"]

        # Build structured context string distinguishing Uploaded Document vs Base KB
        context_lines = []
        doc_sources_present = False
        for s in sources:
            if s.source_type == "uploaded_document":
                doc_sources_present = True
                page_str = f"Page {s.page}" if s.page else "Document"
                sec_str = f", Section: \"{s.section_heading}\"" if s.section_heading else ""
                context_lines.append(f"- [📄 Uploaded Document: {s.document_name} ({page_str}{sec_str})]: {s.snippet}")
            else:
                context_lines.append(f"- [📚 Base Insurance KB: {s.category} / {s.title}]: {s.snippet}")

        context_str = "\n".join(context_lines) if context_lines else "Standard insurance regulations (IRDAI)."

        # Construct Grounded System Prompt
        doc_instruction = ""
        if active_document:
            not_found_msg = NOT_FOUND_IN_DOC_TRANSLATIONS.get(detected_language, NOT_FOUND_IN_DOC_TRANSLATIONS["en"])
            doc_instruction = f"""
SPECIAL INSTRUCTIONS FOR ACTIVE UPLOADED DOCUMENT ('{active_document}'):
- An insurance document has been uploaded by the user: '{active_document}'.
- PREFER the retrieved document context over general knowledge.
- Answer using the retrieved evidence from the document. Cite the page number and section title.
- Do NOT invent or hallucinate information that is not present in the document.
- If the requested information cannot be found in the uploaded document context, explicitly state:
  "{not_found_msg}"
- Clearly distinguish between information found in the uploaded document and general insurance knowledge.
"""

        system_prompt = f"""You are BharatInsure AI, an expert Indian fintech and insurance conversational assistant.
IMPORTANT RULES:
1. You MUST answer directly in {lang_name} ({lang_info['native']}). Use natural, native script.
2. Ground your answer in the following retrieved evidence:
{context_str}
{doc_instruction}
3. Maintain multi-turn conversational context:
{conversation_history_text}
4. When discussing waiting periods, claims, room rent limits, deductibles, or policies, relate them accurately to the context.
5. Never invent policy numbers, specific monetary guarantees, or legal conclusions.
6. Conclude with a brief reminder that this is general information and not legal/financial advice.
User Query: {query}"""

        model_used = ""
        response_text = ""

        # Handling unanswerable query when no matching evidence is found in active uploaded document
        query_words_set = set(re.findall(r'\b\w+\b', query.lower()))
        greeting_tokens = {"hi", "hello", "hey", "help", "வணக்கம்", "नमस्ते", "నమస్కారం", "ನಮಸ್ಕಾರ", "നമസ്കാരം"}
        is_greeting = bool(query_words_set.intersection(greeting_tokens)) or query.strip().lower() in {"who are you", "who r u", "help"}

        if not sources and active_document:
            if is_greeting:
                greeting_text = INDIC_RESPONSES.get(detected_language, INDIC_RESPONSES["en"])["greeting"]
                return {
                    "response": greeting_text,
                    "model_used": "BharatInsure Assistant (Local)",
                    "latency_ms": round((time.time() - start_time) * 1000, 1)
                }
            else:
                not_found_msg = NOT_FOUND_IN_DOC_TRANSLATIONS.get(detected_language, NOT_FOUND_IN_DOC_TRANSLATIONS["en"])
                return {
                    "response": f"{not_found_msg} This topic or condition is not stated in the uploaded policy document ('{active_document}').\n\n**Source limitation:** Not found in any section of the uploaded policy document.",
                    "model_used": "BharatInsure Document Scope Verification (Local)",
                    "latency_ms": round((time.time() - start_time) * 1000, 1)
                }

        # Handling out-of-scope query when no evidence is retrieved and no active document
        if not sources and not active_document:
            if is_greeting:
                greeting_text = INDIC_RESPONSES.get(detected_language, INDIC_RESPONSES["en"])["greeting"]
                return {
                    "response": greeting_text,
                    "model_used": "BharatInsure Assistant (Local)",
                    "latency_ms": round((time.time() - start_time) * 1000, 1)
                }
            else:
                out_msg = OUT_OF_SCOPE_TRANSLATIONS.get(detected_language, OUT_OF_SCOPE_TRANSLATIONS["en"])
                return {
                    "response": out_msg,
                    "model_used": "BharatInsure Scope Verification (Local)",
                    "latency_ms": round((time.time() - start_time) * 1000, 1)
                }

        # 1. Primary path for Real Local LLM via Ollama (qwen2.5:3b)
        if model_preference in ("local_small", "local"):
            try:
                # System prompt optimized for qwen2.5:3b: clear, beginner-friendly, structured, strictly grounded
                if doc_sources_present:
                    local_prompt_system = f"""You are BharatInsure AI, an expert insurance policy document assistant.
Answer in {lang_name} ({lang_info['native']}).

RULES FOR UPLOADED POLICY DOCUMENT Q&A:
1. Answer strictly and only from the Retrieved Policy Evidence below. Do not use outside knowledge or assume coverage.
2. State exact numbers, waiting period durations, rupee amounts, percentages, and limits (e.g., 50%, 100%, 36 months, 24-month, INR 2,50,000, 30 days, 10% co-payment).
3. Exclusions & Exceptions: Dental treatment is permanently excluded EXCEPT when necessitated by accidental injury. Bariatric surgery is permanently excluded EXCEPT when BMI exceeds 40. Never say excluded treatments are generally covered.
4. Waiting Periods: Initial illness waiting period is 30 days. Pre-existing disease waiting period is 36 months. Maternity rider waiting period is 24-month. Specific illnesses (cataract, joint replacement) waiting period is 24-month. Accidental hospitalisation is covered from Day 1.
5. Robotic Surgery: State that a 10% co-payment applies specifically to robotic-assisted surgeries under Clause 4.2 (overriding general 0% co-payment).
6. Rejection Grounds: Explicitly include fraudulent claims or fabricated invoices, non-disclosure of pre-existing diseases, active waiting periods, and excluded hospitals.
7. If the question asks about something not mentioned in the policy document, explicitly state:
   "This information is not stated in the uploaded policy document."
8. Target length: approximately 50-100 words.

Retrieved Policy Evidence:
{context_str}"""
                else:
                    local_prompt_system = f"""You are BharatInsure AI, an expert Indian fintech and insurance conversational assistant.
Answer in {lang_name} ({lang_info['native']}).

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
                    {"role": "system", "content": local_prompt_system},
                    {"role": "user", "content": query}
                ]
                local_res = local_llm_service.generate(messages, max_new_tokens=140)
                response_text = local_res["response"]
                model_used = local_res.get("model_name", f"{local_llm_service.model_name} (Ollama Local LLM - 3.1B Params)")

            except Exception as e:
                print(f"[LLM Manager] Ollama Local LLM error: {e}")
                # Requirement 7 & 13: In local mode, NEVER call cloud models. Use transparent fallback label.
                response_text = self._generate_grounded_indic_response(
                    query=query,
                    lang_code=detected_language,
                    sources=sources,
                    history_text=conversation_history_text,
                    active_document=active_document
                )
                model_used = "Ollama Unavailable — Rule-based fallback (NOT an LLM)"

        # 2. Cloud API Baseline path (only if cloud preference explicitly requested)
        elif model_preference == "api":
            if self.gemini_api_key:
                res = self._call_gemini_rest(system_prompt)
                if res:
                    response_text = res
                    model_used = "Google Gemini 1.5 Flash (Cloud API)"
            elif self.groq_api_key:
                res = self._call_openai_compatible_rest(system_prompt, self.groq_api_key, "https://api.groq.com/openai/v1", "llama-3.1-8b-instant")
                if res:
                    response_text = res
                    model_used = "Groq Llama-3.1-8B (Cloud API)"
            elif self.openai_api_key:
                res = self._call_openai_compatible_rest(system_prompt, self.openai_api_key, "https://api.openai.com/v1", "gpt-4o-mini")
                if res:
                    response_text = res
                    model_used = "OpenAI GPT-4o-mini (Cloud API)"

            # If API was requested but no cloud API key exists, seamlessly run local Ollama
            if not response_text:
                try:
                    if doc_sources_present:
                        local_prompt_system = f"""You are BharatInsure AI, an expert insurance policy document assistant.
Answer in {lang_name} ({lang_info['native']}).

RULES FOR UPLOADED POLICY DOCUMENT Q&A:
1. Answer strictly and only from the Retrieved Policy Evidence below. Do not use outside knowledge or assume coverage.
2. State exact numbers, waiting period durations, rupee amounts, percentages, and limits (e.g., 50%, 100%, 36 months, 24-month, INR 2,50,000, 30 days, 10% co-payment).
3. Exclusions & Exceptions: Dental treatment is permanently excluded EXCEPT when necessitated by accidental injury. Bariatric surgery is permanently excluded EXCEPT when BMI exceeds 40. Never say excluded treatments are generally covered.
4. Waiting Periods: Initial illness waiting period is 30 days. Pre-existing disease waiting period is 36 months. Maternity rider waiting period is 24-month. Specific illnesses (cataract, joint replacement) waiting period is 24-month. Accidental hospitalisation is covered from Day 1.
5. Robotic Surgery: State that a 10% co-payment applies specifically to robotic-assisted surgeries under Clause 4.2 (overriding general 0% co-payment).
6. Rejection Grounds: Explicitly include fraudulent claims or fabricated invoices, non-disclosure of pre-existing diseases, active waiting periods, and excluded hospitals.
7. If the question asks about something not mentioned in the policy document, explicitly state:
   "This information is not stated in the uploaded policy document."
8. Target length: approximately 50-100 words.

Retrieved Policy Evidence:
{context_str}"""
                    else:
                        local_prompt_system = f"""You are BharatInsure AI, an expert Indian fintech and insurance conversational assistant.
Answer in {lang_name} ({lang_info['native']}).

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
                        {"role": "system", "content": local_prompt_system},
                        {"role": "user", "content": query}
                    ]
                    local_res = local_llm_service.generate(messages, max_new_tokens=140)
                    response_text = local_res["response"]
                    model_used = local_res.get("model_name", f"{local_llm_service.model_name} (Ollama Local LLM - 3.1B Params)")

                except Exception as e:
                    print(f"[LLM Manager] Ollama fallback execution error: {e}")
                    response_text = self._generate_grounded_indic_response(
                        query=query,
                        lang_code=detected_language,
                        sources=sources,
                        history_text=conversation_history_text,
                        active_document=active_document
                    )
                    model_used = "Ollama Unavailable — Rule-based fallback (NOT an LLM)"

        # Guarantee page-level citation appended for all document-based responses
        if doc_sources_present:
            doc_sources = [s for s in sources if s.source_type == "uploaded_document"]
            citation_block = self._format_document_citations(doc_sources)
            if citation_block and "**Source:**" not in response_text:
                response_text = response_text.strip() + "\n" + citation_block

        latency_ms = round((time.time() - start_time) * 1000, 1)

        return {
            "response": response_text,
            "model_used": model_used,
            "latency_ms": latency_ms
        }

    def _generate_grounded_indic_response(
        self,
        query: str,
        lang_code: str,
        sources: List[RAGSource],
        history_text: str,
        active_document: Optional[str] = None
    ) -> str:
        """
        Grounded, accurate multilingual response generator tailored for Indian languages.
        Seamlessly integrates uploaded document citations and base knowledge.
        """
        lang = lang_code if lang_code in INDIC_RESPONSES else "en"
        data = INDIC_RESPONSES[lang]
        q_lower = query.lower()

        # Check for uploaded document sources
        doc_sources = [s for s in sources if s.source_type == "uploaded_document"]
        kb_sources = [s for s in sources if s.source_type != "uploaded_document"]

        paragraphs = []

        # If user has an active document and asked a question
        if active_document:
            not_found_msg = NOT_FOUND_IN_DOC_TRANSLATIONS.get(lang, NOT_FOUND_IN_DOC_TRANSLATIONS["en"])

            # Check if document has relevant match (relevance score >= 0.12)
            relevant_doc_sources = [s for s in doc_sources if s.relevance_score >= 0.12]

            if relevant_doc_sources:
                top_doc = relevant_doc_sources[0]
                page_str = f"Page {top_doc.page}" if top_doc.page else ""
                section_str = top_doc.section_heading or "Policy Terms"

                if lang == "ta":
                    header = f"📄 **பதிவேற்றப்பட்ட ஆவணம் ({top_doc.document_name} - {page_str}):**"
                elif lang == "hi":
                    header = f"📄 **अपलोड किया गया दस्तावेज़ ({top_doc.document_name} - {page_str}):**"
                elif lang == "te":
                    header = f"📄 **అప్‌లోడ్ చేసిన పత్రం ({top_doc.document_name} - {page_str}):**"
                elif lang == "kn":
                    header = f"📄 **ಅಪ್‌ಲೋಡ್ ಮಾಡಿದ ದಾಖಲೆ ({top_doc.document_name} - {page_str}):**"
                elif lang == "ml":
                    header = f"📄 **അപ്‌ലോഡ് ചെയ്ത രേഖ ({top_doc.document_name} - {page_str}):**"
                else:
                    header = f"📄 **Uploaded Document ({top_doc.document_name} - {page_str}):**"

                paragraphs.append(f"{header}\n{top_doc.snippet}")

                # Format exact page-level citation according to Requirement 4
                citation_block = self._format_document_citations(relevant_doc_sources)
                if citation_block:
                    paragraphs.append(citation_block.strip())

            else:
                # Question is not covered in the uploaded document
                paragraphs.append(f"ℹ️ {not_found_msg} This topic is not stated in the uploaded policy document ('{active_document}').\n\n**Source limitation:** Not found in any section of the uploaded policy document.")

                # Supplement with general KB if available
                if kb_sources and kb_sources[0].relevance_score >= 0.15:
                    top_kb = kb_sources[0]
                    if lang == "ta":
                        kb_note = f"📚 **பொதுவான காப்பீட்டு அறிவு ({top_kb.category}):**\n{top_kb.snippet}"
                    elif lang == "hi":
                        kb_note = f"📚 **सामान्य बीमा नियम ({top_kb.category}):**\n{top_kb.snippet}"
                    else:
                        kb_note = f"📚 **General Insurance Knowledge ({top_kb.category}):**\n{top_kb.snippet}"
                    paragraphs.append(kb_note)
                elif "waiting" in q_lower or "pre-existing" in q_lower or "ped" in q_lower:
                    paragraphs.append(data["waiting_period"])
                elif "room" in q_lower or "rent" in q_lower:
                    paragraphs.append(
                        "Standard IRDAI room rent guidelines: Most policies cap normal room rent at 1% of Sum Assured and ICU at 2% unless a 'No Room Rent Capping' rider is selected."
                        if lang == "en" else data["health_intro"]
                    )
                else:
                    paragraphs.append(data["health_intro"])

            paragraphs.append(f"\n⚠️ {data['disclaimer']}")
            return "\n\n".join(paragraphs)

        # Base KB standard flow when no document is active
        is_waiting = any(w in query for w in ["காத்திருப்பு", "प्रतीक्षा", "waiting", "ped", "pre-existing", "நோய்", "ಅವಧಿ", "కాలపరిమితి"]) or ("waiting" in q_lower)
        is_claim = any(w in query for w in ["claim", "உரிமைகோ", "दावा", "ക്ലെയിം", "ಕ್ಲೈಮ್", "ಕ್ಲೇಮ್", "క్లెయిమ్", "cashless", "reimbursement"]) or ("claim" in q_lower)
        is_health = any(w in query for w in ["மருத்துவ", "health", "mediclaim", "மருத்துவம்", "स्वास्थ्य", "hospital", "ஆரோக்கிய", "ಆರೋಗ್ಯ", "ആരോഗ്യ", "ఆరోగ్య", "ஹெல்த்", "हेल्थ", "room", "rent", "copay"])
        is_motor = any(w in query for w in ["வாகனம்", "கார்", "गाड़ी", "motor", "car", "bike", "third party", "zero dep", "வாഹനം", "వాహனம்", "ವಾಹನ", "idv", "own damage"])
        is_life = any(w in query for w in ["ஆயுள்", "வாழ்நாள்", "जीवन", "life", "term", "sum assured", "nominee", "ಟರಮ್", "ജീവിത", "జీవిత"])

        if sources:
            top_src = sources[0]
            cat = top_src.category
            title = top_src.title
            snippet = top_src.snippet

            if lang == "ta":
                header = f"📚 **[IRDAI அறிவுத்தளம்: {cat} - {title}]:**"
            elif lang == "hi":
                header = f"📚 **[IRDAI ज्ञानकोष: {cat} - {title}]:**"
            elif lang == "te":
                header = f"📚 **[IRDAI నాలెడ్జ్ బేస్: {cat} - {title}]:**"
            elif lang == "kn":
                header = f"📚 **[IRDAI ಜ್ಞಾನಕೋಶ: {cat} - {title}]:**"
            elif lang == "ml":
                header = f"📚 **[IRDAI നോളജ് ബേസ്: {cat} - {title}]:**"
            else:
                header = f"📚 **[IRDAI Knowledge Base: {cat} - {title}]:**"

            if is_waiting and "waiting_period" in data:
                paragraphs.append(data["waiting_period"])
            elif is_health and "health_intro" in data:
                paragraphs.append(data["health_intro"])
            elif is_motor and "motor" in data:
                paragraphs.append(data["motor"])
            elif is_life and "life" in data:
                paragraphs.append(data["life"])
            elif is_claim and "claims" in data:
                paragraphs.append(data["claims"])

            paragraphs.append(f"{header}\n{snippet}")

            if len(sources) > 1:
                sec = sources[1]
                paragraphs.append(f"📌 **{sec.title}**:\n{sec.snippet}")
        else:
            is_greeting = any(w in q_lower for w in ["hi", "hello", "hey", "வணக்கம்", "नमस्ते", "నమస్కారం", "ನಮಸ್ಕಾರ", "നമസ്കാരം", "help", "who are you"]) or len(query.strip().split()) <= 2
            if is_greeting:
                paragraphs.append(data["greeting"])
            else:
                paragraphs.append(OUT_OF_SCOPE_TRANSLATIONS.get(lang, OUT_OF_SCOPE_TRANSLATIONS["en"]))

        # Localized disclaimer
        paragraphs.append(f"\n⚠️ {data['disclaimer']}")

        return "\n\n".join(paragraphs)

# Singleton instance
llm_manager = LLMManager()
