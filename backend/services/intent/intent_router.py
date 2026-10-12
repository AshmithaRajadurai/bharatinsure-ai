"""
Lightweight Intent Router for BharatInsure AI.
Instantly handles basic conversational intents (greetings, chatbot identity, capabilities)
without incurring RAG retrieval overhead or local LLM CPU latency.

STRICT GUARDRAIL: Any query mentioning insurance, policy, financial terms, or uploaded documents
is ALWAYS routed to retrieval and domain grounding.
"""

import re
from typing import Optional, Dict, Any, Tuple

# Domain keywords that MUST NEVER be bypassed by intent routing
DOMAIN_INDICATORS = {
    # English terms
    "insurance", "policy", "policies", "health", "life", "motor", "car", "bike", "vehicle",
    "travel", "claim", "claims", "cashless", "reimbursement", "waiting period", "ped",
    "pre-existing", "disease", "hospital", "hospitalization", "icu", "room rent", "copay",
    "co-payment", "deductible", "premium", "lapse", "grace period", "free look", "surrender",
    "term", "nominee", "section 39", "section 45", "mwpa", "ombudsman", "grievance", "irdai",
    "upi", "autopay", "vpa", "qr", "pin", "banking", "bank", "savings", "current account",
    "fixed deposit", "fd", "recurring deposit", "rd", "interest", "dicgc", "loan", "emi",
    "home loan", "ltv", "cibil", "credit score", "credit card", "investment", "mutual fund",
    "sip", "swp", "nav", "stock", "bond", "sgb", "g-sec", "inflation", "budget", "emergency fund",
    "fraud", "scam", "cyber", "phishing", "1930", "kyc", "aadhaar", "pan", "tax", "80c", "80d",
    "document", "uploaded", "clause", "coverage", "exclusion", "robotic", "bariatric", "dental",
    "accident", "maternity", "ayush", "tpa", "neft", "rtgs", "imps",
    # Indic roots
    "காப்பீடு", "மருத்துவ", "ஆயுள்", "வாகன", "கிளைம்", "பணம்", "கடன்", "வங்கி", "வைப்பு", "மோசடி",
    "बीमा", "स्वास्थ्य", "जीवन", "मोटर", "क्लेम", "ऋण", "लोन", "बैंक", "बचत", "जमा", "धोखाधड़ी",
    "బీమా", "ఆరోగ్య", "జీవిత", "క్లెయిమ్", "రుణం", "బ్యాంక్", "డిపాజిట్",
    "ವಿಮೆ", "ಆರೋಗ್ಯ", "ಜೀವ", "ಕ್ಲೈಮ್", "ಸಾಲ", "ಬ್ಯಾಂಕ್", "ಠೇವಣಿ",
    "ഇൻഷുറൻസ്", "ആരോഗ്യ", "ലൈഫ്", "ക്ലെയിം", "വായ്പ", "ബാങ്ക്", "നിക്ഷേപം"
}

PREDEFINED_RESPONSES = {
    "greeting": {
        "en": "Hello! I am BharatInsure AI – your Multilingual Indian Insurance & Fintech Assistant. How can I help you today with Health, Life, Motor Insurance, Claims, Banking, or Digital Payments?",
        "hi": "नमस्ते! मैं भारत इंश्योरेंस एआई (BharatInsure AI) हूँ – आपका बहुभाषी बीमा और फिनटेक सहायक। आज मैं स्वास्थ्य, जीवन, मोटर बीमा, क्लेम, बैंकिंग या डिजिटल भुगतान में आपकी क्या सहायता कर सकता हूँ?",
        "ta": "வணக்கம்! நான் பாரத் இன்ஷூரன்ஸ் AI (BharatInsure AI) – உங்கள் பன்மொழி இந்திய காப்பீடு மற்றும் நிதி உதவியாளர். மருத்துவ காப்பீடு, ஆயுள் காப்பீடு, வாகன காப்பீடு, கிளைம்கள், வங்கி அல்லது டிஜிட்டல் பேமெண்ட்கள் பற்றி உங்களுக்கு எவ்வாறு உதவ முடியும்?",
        "te": "నమస్కారం! నేను భారత్ ఇన్సూరెన్స్ AI – మీ బహుభాషా భారతీయ బీమా మరియు ఫిన్‌టెక్ సహాయకుడిని. ఆరోగ్య, జీవిత, మోటార్ బీమా, క్లెయిమ్‌లు, బ్యాంకింగ్ లేదా డిజిటల్ చెల్లింపులపై మీకు ఎలా సహాయం చేయగలను?",
        "kn": "ನಮಸ್ಕಾರ! ನಾನು ಭಾರತ್ ಇನ್ಶೂರೆನ್ಸ್ AI – ನಿಮ್ಮ ಬಹುಭಾಷಾ ಭಾರತೀಯ ವಿಮಾ ಮತ್ತು ಫಿನ್‌ಟೆಕ್ ಸಹಾಯಕ. ಆರೋಗ್ಯ, ಜೀವ, ವಾಹನ ವಿಮೆ, ಕ್ಲೈಮ್‌ಗಳು, ಬ್ಯಾಂಕಿಂಗ್ ಅಥವಾ ಡಿಜಿಟಲ್ ಪಾವತಿಗಳಲ್ಲಿ ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?",
        "ml": "നമസ്കാരം! ഞാൻ ഭാരത് ഇൻഷുറൻസ് AI – നിങ്ങളുടെ ബഹുഭാഷാ ഇന്ത്യൻ ഇൻഷുറൻസ്, ഫിൻടെക് സഹായി. ആരോഗ്യ, ജീവൻ, വാഹന ഇൻഷുറൻസ്, ക്ലെയിമുകൾ, ബാങ്കിംഗ് അല്ലെങ്കിൽ ഡിജിറ്റൽ പേയ്‌മെന്റുകൾ എന്നിവയിൽ ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?"
    },
    "identity": {
        "en": "I am BharatInsure AI, an intelligent conversational assistant specialized in Indian insurance policies and personal finance. I help you understand:\n• Health, Life, Motor, and Travel insurance coverage\n• IRDAI guidelines, waiting periods, room rent caps, and exclusions\n• Claim settlement processes (Cashless vs Reimbursement)\n• Uploaded policy document analysis with exact clause citations\n• Indian fintech concepts: UPI, banking deposits, loans, EMIs, CIBIL, and investments.",
        "hi": "मैं भारत इंश्योरेंस एआई (BharatInsure AI) हूँ, जो भारतीय बीमा पॉलिसियों और व्यक्तिगत वित्त पर विशेषज्ञता रखने वाला एक बुद्धिमान संवादात्मक सहायक है। मैं आपकी सहायता करता हूँ:\n• स्वास्थ्य, जीवन, मोटर और यात्रा बीमा कवरेज समझने में\n• IRDAI दिशानिर्देश, प्रतीक्षा अवधि और बहिष्करण (Exclusions)\n• कैशलेस और रीइंबर्समेंट क्लेम प्रक्रिया में\n• अपलोड किए गए पॉलिसी दस्तावेज़ों का सटीक विश्लेषण करने में\n• यूपीआई (UPI), बैंक जमा, ऋण (Loans), सिबिल और म्यूचुअल फंड में।",
        "ta": "நான் பாரத் இன்ஷூரன்ஸ் AI (BharatInsure AI). இந்திய காப்பீட்டுக் கொள்கைகள் மற்றும் தனிநபர் நிதி சார்ந்த வழிகாட்டுதல்களை வழங்கும் பிரத்யேக AI உதவியாளர். எனது முக்கிய பணிகள்:\n• மருத்துவ, ஆயுள், மோட்டார் மற்றும் பயண காப்பீட்டு விவரங்களை விளக்குதல்\n• IRDAI விதிகள், காத்திருப்பு காலங்கள் (Waiting Periods) மற்றும் நிபந்தனைகள்\n• கேஷ்லெஸ் மற்றும் ரீஇம்பர்ஸ்மென்ட் கிளைம் வழிகாட்டுதல்\n• பதிவேற்றப்பட்ட பாலிசி ஆவணங்களை பகுப்பாய்வு செய்து பக்க மேற்கோள்களுடன் பதிலளித்தல்\n• UPI, வங்கி சேமிப்பு, கடன்கள், சிபில் மற்றும் மியூச்சுவல் ஃபண்ட் தகவல்கள்.",
        "te": "నేను భారత్ ఇన్సూరెన్స్ AI. భారతీయ బీమా పాలసీలు మరియు వ్యక్తిగత ఆర్థిక రంగంలో సహాయపడే ప్రత్యేక AI అసిస్టెంట్. నేను మీకు వీటిలో సహాయపడతాను:\n• ఆరోగ్య, జీవిత, మోటార్ బీమా కవరేజ్ వివరాలు\n• IRDAI నిబంధనలు, వేచి ఉండే కాలం మరియు మినహాయింపులు\n• క్యాష్‌లెస్ మరియు రీయింబర్స్‌మెంట్ క్లెయిమ్ విధానం\n• అప్‌లోడ్ చేసిన పాలసీ పత్రాల విశ్లేషణ\n• UPI, బ్యాంకింగ్, రుణాలు మరియు పెట్టుబడులు.",
        "kn": "ನಾನು ಭಾರತ್ ಇನ್ಶೂರೆನ್ಸ್ AI. ಭಾರತೀಯ ವಿಮಾ ಪಾಲಿಸಿಗಳು ಮತ್ತು ವೈಯಕ್ತಿಕ ಹಣಕಾಸು ಕುರಿತು ಮಾರ್ಗದರ್ಶನ ನೀಡುವ AI ಸಹಾಯಕ. ನಾನು ಈ ಕೆಳಗಿನವುಗಳಲ್ಲಿ ಸಹಾಯ ಮಾಡುತ್ತೇನೆ:\n• ಆರೋಗ್ಯ, ಜೀವ, ವಾಹನ ವಿಮೆ ಮಾಹಿತಿ\n• IRDAI ನಿಯಮಗಳು, ಕಾಯುವ ಅವಧಿ ಮತ್ತು ವಿನಾಯಿತಿಗಳು\n• ಕ್ಯಾಶ್‌ಲೆಸ್ ಮತ್ತು ಮರುಪಾವತಿ ಕ್ಲೈಮ್ ಪ್ರಕ್ರಿಯೆ\n• ಅಪ್‌ಲೋಡ್ ಮಾಡಿದ ಪಾಲಿಸಿ ದಾಖಲೆಗಳ ನಿಖರ ವಿಶ್ಲೇಷಣೆ\n• UPI, ಬ್ಯಾಂಕಿಂಗ್, ಸಾಲಗಳು ಮತ್ತು ಹೂಡಿಕೆಗಳು.",
        "ml": "ഞാൻ ഭാരത് ഇൻഷുറൻസ് AI ആണ്. ഇന്ത്യൻ ഇൻഷുറൻസ് പോളിസികളിലും വ്യക്തിഗത ധനകാര്യത്തിലും സഹായിക്കുന്ന സമർപ്പിത AI സഹായി. എന്റെ പ്രധാന സേവനങ്ങൾ:\n• ആരോഗ്യ, ജീവൻ, വാഹന ഇൻഷുറൻസ് വിശദാംശങ്ങൾ\n• IRDAI നിയമങ്ങൾ, കാത്തിരിപ്പ് കാലയളവ്, ഒഴിവാക്കലുകൾ\n• ക്യാഷ്‌ലെസ്സ്, റീഇംബേഴ്സ്മെന്റ് ക്ലെയിം പ്രക്രിയകൾ\n• അപ്‌ലോഡ് ചെയ്ത പോളിസി രേഖകളുടെ കൃത്യമായ വിശകലനം\n• UPI, ബാങ്കിംഗ്, വായ്പകൾ, നിക്ഷേപങ്ങൾ."
    },
    "capabilities": {
        "en": "Here is what I can do for you:\n1. 📋 **Explain Policies:** Break down health, life, motor, and travel insurance in simple language.\n2. ⏱️ **Waiting Periods & Clauses:** Clarify initial 30-day, pre-existing disease (PED), and maternity waiting periods.\n3. 🏥 **Claims Assistance:** Step-by-step guidance for Cashless hospitalisation and Reimbursement claims.\n4. 📄 **Document Analysis:** Upload your insurance policy PDF/DOCX to get exact clause citations and answers.\n5. 💳 **Fintech & Banking:** Answers on UPI, loans, EMIs, credit scores (CIBIL), fixed deposits, and cyber fraud helpline (1930).\n\nFeel free to ask any question or upload your policy document to begin!",
        "hi": "यहाँ बताया गया है कि मैं आपकी क्या मदद कर सकता हूँ:\n1. 📋 **पॉलिसी समझें:** स्वास्थ्य, जीवन, मोटर और यात्रा बीमा को सरल भाषा में समझें।\n2. ⏱️ **प्रतीक्षा अवधि और शर्तें:** 30 दिन की शुरुआती प्रतीक्षा अवधि, पहले से मौजूद बीमारियों (PED) और मातृत्व शर्तों की स्पष्टता।\n3. 🏥 **क्लेम सहायता:** कैशलेस अस्पताल भर्ती और रीइंबर्समेंट क्लेम की चरणबद्ध जानकारी।\n4. 📄 **दस्तावेज़ विश्लेषण:** अपनी पॉलिसी PDF/DOCX अपलोड करें और सटीक क्लॉज संदर्भों के साथ उत्तर प्राप्त करें।\n5. 💳 **फिनटेक और बैंकिंग:** UPI, लोन, EMI, सिबिल स्कोर, फिक्स्ड डिपॉजिट और साइबर हेल्पलाइन (1930)।",
        "ta": "நான் உங்களுக்கு செய்யும் முக்கிய உதவிகள்:\n1. 📋 **பாலிசி விளக்கம்:** மருத்துவ, ஆயுள் மற்றும் மோட்டார் காப்பீட்டு விதிமுறைகளை எளிய மொழியில் அறிதல்.\n2. ⏱️ **காத்திருப்பு காலம்:** 30 நாள் ஆரம்ப காத்திருப்பு காலம், ஏற்கனவே உள்ள நோய்கள் (PED) மற்றும் பேறுகால விதிமுறைகள்.\n3. 🏥 **கிளைம் உதவி:** கேஷ்லெஸ் மற்றும் ரீஇம்பர்ஸ்மென்ட் கிளைம்களுக்கான எளிய வழிமுறைகள்.\n4. 📄 **ஆவண பகுப்பாய்வு:** உங்கள் பாலிசி PDF/DOCX ஆவணத்தை பதிவேற்றி குறிப்பிட்ட விதிமுறைகளை கண்டறிதல்.\n5. 💳 **வங்கி & நிதி:** UPI, கடன்கள், தவணை (EMI), சிபில் ஸ்கோர் மற்றும் சைபர் மோசடி உதவி எண் (1930).",
        "te": "నేను మీకు అందించే సహాయాలు:\n1. 📋 **పాలసీల వివరణ:** ఆరోగ్య, జీవిత మరియు మోటార్ బీమా వివరాలు సులభంగా తెలుసుకోండి.\n2. ⏱️ **వేచి ఉండే కాలం:** 30 రోజుల ప్రారంభ సమయం మరియు ముందున్న వ్యాధుల (PED) నిబంధనలు.\n3. 🏥 **క్లెయిమ్ సహాయం:** క్యాష్‌లెస్ మరియు రీయింబర్స్‌మెంట్ పూర్తి సమాచారం.\n4. 📄 **డాక్యుమెంట్ విశ్లేషణ:** మీ పాలసీ పత్రాన్ని అప్‌లోడ్ చేసి సమాధానాలు పొందండి.\n5. 💳 **ఫిన్‌టెక్:** UPI, లోన్లు, EMI, సిబిల్ స్కోర్ మరియు సైబర్ హెల్ప్‌లైన్ (1930).",
        "kn": "ನಾನು ನಿಮಗೆ ನೀಡುವ ಪ್ರಮುಖ ನೆರವುಗಳು:\n1. 📋 **ಪಾಲಿಸಿ ವಿವರಣೆ:** ಆರೋಗ್ಯ, ಜೀವ ಮತ್ತು ವಾಹನ ವಿಮೆ ನಿಯಮಗಳ ಸುಲಭ ವಿವರಣೆ.\n2. ⏱️ **ಕಾಯುವ ಅವಧಿ:** 30 ದಿನಗಳ ಆರಂಭಿಕ ಕಾಯುವಿಕೆ ಮತ್ತು ಮೊದಲೇ ಇರುವ ರೋಗಗಳ (PED) ನಿಯಮಗಳು.\n3. 🏥 **ಕ್ಲೈಮ್ ನೆರವು:** ಕ್ಯಾಶ್‌ಲೆಸ್ ಮತ್ತು ಮರುಪಾವತಿ ಕ್ಲೈಮ್ ಪ್ರಕ್ರಿಯೆ.\n4. 📄 **ದಾಖಲೆ ವಿಶ್ಲೇಷಣೆ:** ನಿಮ್ಮ ಪಾಲಿಸಿ PDF ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ಉತ್ತರ ಪಡೆಯಿರಿ.\n5. 💳 **ಫಿನ್‌ಟೆಕ್:** UPI, ಸಾಲಗಳು, EMI, ಸಿಬಿಲ್ ಸ್ಕೋರ್ ಮತ್ತು ಸೈಬರ್ ಹೆಲ್ಪ್‌ಲೈನ್ (1930).",
        "ml": "ഞാൻ നൽകുന്ന പ്രധാന സേവനങ്ങൾ:\n1. 📋 **പോളിസി വിശദീകരണം:** ആരോഗ്യ, ലൈഫ്, മോട്ടോർ ഇൻഷുറൻസ് വിവരങ്ങൾ ലളിതമായി അറിയുക.\n2. ⏱️ **കാത്തിരിപ്പ് കാലാവധി:** 30 ദിവസത്തെ പ്രാരംഭ കാലയളവ്, മുൻപുണ്ടായിരുന്ന രോഗങ്ങളുടെ (PED) വ്യവസ്ഥകൾ.\n3. 🏥 **ക്ലെയിം സഹായം:** ക്യാഷ്‌ലെസ്സ്, റീഇംബേഴ്സ്മെന്റ് ക്ലെയിം വിവരങ്ങൾ.\n4. 📄 **ഡോക്യുമെന്റ് വിശകലനം:** പോളിസി PDF അപ്‌ലോഡ് ചെയ്ത് കൃത്യമായ വിവരങ്ങൾ കണ്ടെത്തുക.\n5. 💳 **ഫിൻടെക്:** UPI, വായ്പകൾ, EMI, സിബിൽ സ്കോർ, സൈബർ ഹെൽപ്പ് ലൈൻ (1930)."
    }
}

GREETING_PATTERNS = [
    r"^(hi|hello|hey|hiya|howdy)[\s!.]*$",
    r"^(good\s+(morning|afternoon|evening|day))[\s!.]*$",
    r"^(greetings|namaste|vanakkam|namaskaram|namaskara)[\s!.]*$",
    r"^(வணக்கம்|ஹலோ)[\s!.]*$",
    r"^(नमस्ते|नमस्कार|प्रणाम|हेलो|हाय)[\s!.]*$",
    r"^(నమస్కారం|హలో|హాయ్)[\s!.]*$",
    r"^(ನಮಸ್ಕಾರ|ಹಲೋ|ಹಾಯ್)[\s!.]*$",
    r"^(നമസ്കാരം|ഹലോ|ഹായ്)[\s!.]*$"
]

IDENTITY_PATTERNS = [
    r"^(who\s+are\s+you|who\s+r\s+u|what\s+is\s+your\s+name|what\s+are\s+you|tell\s+me\s+about\s+yourself)[\s?!.]*$",
    r"^(who\s+(made|created|built)\s+you|are\s+you\s+(an?\s+)?(ai|bot|robot))[\s?!.]*$",
    r"^(what\s+is\s+bharatinsure(\s+ai)?)[\s?!.]*$",
    r"^(நீ\s+யார்|யார்\s+நீ|உங்கள்\s+பெயர்\s+என்ன|பாரத்\s+இன்ஷூரன்ஸ்\s+என்றால்\s+என்ன)[\s?!.]*$",
    r"^(आप\s+कौन\s+हैं|तुम\s+कौन\s+हो|आपका\s+नाम\s+क्या\s+है|भारत\s+इंश्योरेंस\s+क्या\s+है)[\s?!.]*$",
    r"^(మీరు\s+ఎవరు|నీవు\s+ఎవరు|మీ\s+పేరు\s+ఏమిటి|భారత్\s+ఇన్సూరెన్స్\s+అంటే\s+ఏమిటి)[\s?!.]*$",
    r"^(ನೀವು\s+ಯಾರು|ನಿಮ್ಮ\s+ಹೆಸರೇನು|ಭಾರತ್\s+ಇನ್ಶೂರೆನ್ಸ್\s+ಎಂದರೇನು)[\s?!.]*$",
    r"^(ആരാണ്\s+നിങ്ങൾ|നിങ്ങളുടെ\s+പേരെന്താണ്|ഭാരത്\s+ഇൻഷുറൻസ്\s+എന്നാൽ\s+എന്താണ്)[\s?!.]*$"
]

CAPABILITY_PATTERNS = [
    r"^(what\s+can\s+you\s+do|how\s+can\s+you\s+help(\s+me)?|what\s+are\s+your\s+features|what\s+do\s+you\s+support)[\s?!.]*$",
    r"^(help(\s+me)?|how\s+to\s+use|what\s+services\s+do\s+you\s+provide|features)[\s?!.]*$",
    r"^(உன்னால்\s+என்ன\s+செய்ய\s+முடியும்|எப்படி\s+உதவுவீர்கள்|உதவி)[\s?!.]*$",
    r"^(आप\s+क्या\s+कर\s+सकते\s+हैं|आप\s+कैसे\s+मदद\s+कर\s+सकते\s+हैं|मदद|सहायता)[\s?!.]*$",
    r"^(మీరు\s+ఏమి\s+చేయగలరు|ఎలా\s+సహాయం\s+చేస్తారు|సహాయం)[\s?!.]*$",
    r"^(ನೀವು\s+ಏನು\s+ಮಾಡಬಹುದು|ಹೇಗೆ\s+ಸಹಾಯ\s+ಮಾಡುತ್ತೀರಿ|ಸಹಾಯ)[\s?!.]*$",
    r"^(നിങ്ങൾക്ക്\s+എന്ത്\s+ചെയ്യാൻ\s+കഴിയും|എങ്ങനെ\s+സഹായിക്കും|സഹായം)[\s?!.]*$"
]

class IntentRouter:
    """Fast, zero-latency regex intent router for basic queries."""

    @staticmethod
    def _contains_domain_terms(clean_query: str) -> bool:
        """Checks whether the query contains domain fintech or insurance concepts."""
        words = set(re.findall(r"[\w]+", clean_query.lower()))
        # Check single words
        if bool(words.intersection(DOMAIN_INDICATORS)):
            return True
        # Check phrases
        query_lower = clean_query.lower()
        multiword_terms = [
            "waiting period", "room rent", "cashless", "pre-existing", "home loan",
            "credit score", "fixed deposit", "recurring deposit", "mutual fund",
            "emergency fund", "credit card", "grace period", "free look"
        ]
        return any(term in query_lower for term in multiword_terms)

    @classmethod
    def route(cls, query: str, detected_language: str = "en") -> Optional[Dict[str, Any]]:
        """
        Evaluate user query. Returns predefined response dict if matched, or None
        if query should proceed to RAG and LLM.
        """
        if not query or not query.strip():
            return None

        clean = query.strip()
        clean_lower = clean.lower()

        # 1. STRICT DOMAIN GUARD: If query contains finance/insurance concepts, NEVER route to basic predefined response!
        if cls._contains_domain_terms(clean):
            return None

        # Resolve language code fallback
        lang = detected_language if detected_language in ("en", "hi", "ta", "te", "kn", "ml") else "en"

        # 2. Check Greetings
        for pat in GREETING_PATTERNS:
            if re.match(pat, clean_lower, re.IGNORECASE):
                return {
                    "intent": "greeting",
                    "response": PREDEFINED_RESPONSES["greeting"].get(lang, PREDEFINED_RESPONSES["greeting"]["en"]),
                    "model_used": "BharatInsure Fast Intent Router (Predefined)",
                    "bypassed_rag": True,
                    "bypassed_llm": True
                }

        # 3. Check Bot Identity
        for pat in IDENTITY_PATTERNS:
            if re.match(pat, clean_lower, re.IGNORECASE):
                return {
                    "intent": "identity",
                    "response": PREDEFINED_RESPONSES["identity"].get(lang, PREDEFINED_RESPONSES["identity"]["en"]),
                    "model_used": "BharatInsure Fast Intent Router (Predefined)",
                    "bypassed_rag": True,
                    "bypassed_llm": True
                }

        # 4. Check Capabilities / Help
        for pat in CAPABILITY_PATTERNS:
            if re.match(pat, clean_lower, re.IGNORECASE):
                return {
                    "intent": "capabilities",
                    "response": PREDEFINED_RESPONSES["capabilities"].get(lang, PREDEFINED_RESPONSES["capabilities"]["en"]),
                    "model_used": "BharatInsure Fast Intent Router (Predefined)",
                    "bypassed_rag": True,
                    "bypassed_llm": True
                }

        return None

# Singleton instance
intent_router = IntentRouter()
