"""
High-Precision Multilingual Hybrid RAG Retriever for BharatInsure AI.
Features:
1. Multi-field weighted indexing (Title, Questions, Keywords, Category, Content).
2. Domain-generic word suppression (prevents generic terms like 'insurance' from dominating).
3. Cross-lingual Indic concept expansion for Tamil, Hindi, Telugu, Kannada, Malayalam.
4. Hybrid Scoring: TF-IDF (0.50) + Semantic/N-gram Overlap (0.30) + Keyword/Phrase Match (0.20).
5. Dynamic Relevance Threshold (DO NOT FORCE TOP 3: filters out low-scoring irrelevant chunks).
"""

import re
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.services.rag.knowledge_loader import load_all_knowledge_documents
from backend.models.schemas import RAGSource

# Configurable hybrid parameters and relevance threshold
DEFAULT_HYBRID_CONFIG = {
    "weight_tfidf": 0.50,
    "weight_semantic": 0.30,
    "weight_keyword": 0.20,
    "min_relevance_threshold": 0.25,  # Chunks scoring below this are strictly filtered out
    "max_top_k": 3
}

# Generic domain stopwords that should NOT artificially trigger specific chunk retrieval
DOMAIN_GENERIC_WORDS = {
    "insurance", "policy", "policies", "cover", "coverage", "find", "finding",
    "look", "looking", "new", "want", "tell", "give", "need", "please", "can",
    "what", "how", "details", "information", "about", "me", "is", "are", "the",
    "for", "of", "and", "in", "to", "a", "an", "do", "does", "get", "best", "some",
    "plan", "plans", "i", "my", "we", "our", "there", "it",
    "explain", "simple", "words", "meaning", "define", "know", "describe", "means", "say"
}

# Indic concept expansion dictionary mapping Indian language terminology to insurance and finance concepts
INDIC_CONCEPT_SYNONYMS = {
    # Fintech & UPI & Payments
    "upi": "UPI unified payments interface NPCI VPA digital payments autopay",
    "யுபிஐ": "UPI unified payments interface NPCI VPA digital payments",
    "यूपीआई": "UPI unified payments interface NPCI VPA digital payments",
    "యూపీఐ": "UPI unified payments interface NPCI VPA digital payments",
    "ಯುಪಿಐ": "UPI unified payments interface NPCI VPA digital payments",
    "യുപിഐ": "UPI unified payments interface NPCI VPA digital payments",
    "மோசடி": "fraud scam cybersecurity cybercrime phishing helpline 1930",
    "धोखाधड़ी": "fraud scam cybersecurity cybercrime phishing helpline 1930",
    "మోసం": "fraud scam cybersecurity cybercrime helpline 1930",
    "ಹಗರಣ": "fraud scam cybersecurity cybercrime helpline 1930",
    "തട്ടിപ്പ്": "fraud scam cybersecurity cybercrime helpline 1930",

    # Banking & Deposits
    "சேமிப்பு கணக்கு": "savings account bank deposit interest passbook",
    "நடப்பு கணக்கு": "current account business overdraft bank",
    "பிக்சட் டெபாசிட்": "fixed deposit FD term deposit DICGC interest",
    "நிரந்தர வைப்பு": "fixed deposit FD term deposit interest",
    "தொடர் வைப்பு": "recurring deposit RD monthly deposit tenure",
    "வங்கி": "bank banking savings deposit account branch",
    "बचत खाता": "savings account bank deposit interest",
    "चालू खाता": "current account business overdraft bank",
    "फिक्स्ड डिपॉजिट": "fixed deposit FD term deposit DICGC",
    "सावधि जमा": "fixed deposit FD term deposit DICGC",
    "रेकरिंग डिपॉजिट": "recurring deposit RD monthly installment",
    "आवर्ती जमा": "recurring deposit RD monthly installment",
    "బ్యాంక్ ఖాతా": "savings account current account bank deposit",
    "స్థిర ಠೇವಣಿ": "fixed deposit FD term deposit",
    "ಆವರ್ತಕ ಠೇವಣಿ": "recurring deposit RD monthly installment",
    "സ്ഥിര നിക്ഷേപം": "fixed deposit FD term deposit",
    "ആവർത്തന നിക്ഷേപം": "recurring deposit RD monthly installment",

    # Loans & EMI
    "கடன்": "loan lending EMI interest principal secured unsecured",
    "வீட்டுக் கடன்": "home loan housing mortgage LTV Section 24b 80C",
    "இஎம்ஐ": "EMI equated monthly instalment principal interest amortisation",
    "தவணை": "EMI instalment amortisation monthly payment",
    "ऋण": "loan lending EMI interest principal",
    "होम लोन": "home loan housing mortgage LTV",
    "गृह ऋण": "home loan housing mortgage LTV",
    "ईएमआई": "EMI equated monthly instalment principal interest amortisation",
    "मासिक किस्त": "EMI instalment amortisation monthly payment",
    "రుణం": "loan lending EMI interest principal",
    "హోమ్ లోన్": "home loan housing mortgage",
    "ఈఎంఐ": "EMI equated monthly instalment",
    "ಸಾಲ": "loan lending EMI interest principal",
    "ಗೃಹ ಸಾಲ": "home loan housing mortgage",
    "ಇಎಂಐ": "EMI equated monthly instalment",
    "വായ്പ": "loan lending EMI interest principal",
    "ഭവന വായ്പ": "home loan housing mortgage",
    "ഇഎംഐ": "EMI equated monthly instalment",

    # Credit & Cards
    "கிரெடிட் ஸ்கோர்": "credit score CIBIL Experian credit bureau repayment",
    "சிபில்": "CIBIL credit score credit report bureau",
    "கிரெடிட் கார்டு": "credit card billing cycle grace period minimum amount due",
    "கடன் அட்டை": "credit card billing cycle grace period",
    "क्रेडिट स्कोर": "credit score CIBIL Experian credit bureau repayment",
    "सिबिल": "CIBIL credit score credit report bureau",
    "क्रेडिट कार्ड": "credit card billing cycle grace period minimum amount due",
    "క్రెడిట్ స్కోరు": "credit score CIBIL Experian credit bureau",
    "క్రెడిట్ కార్డు": "credit card billing cycle grace period",
    "ಕ್ರೆಡಿಟ್ ಸ್ಕೋರ್": "credit score CIBIL Experian credit bureau",
    "ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್": "credit card billing cycle grace period",
    "ക്രെഡിറ്റ് സ്കോർ": "credit score CIBIL Experian credit bureau",
    "ക്രെഡിറ്റ് കാർഡ്": "credit card billing cycle grace period",

    # Investments & Wealth
    "மியூச்சுவல் ஃபண்ட்": "mutual fund SIP NAV equity debt index fund AMC",
    "எஸ்ஐபி": "SIP systematic investment plan rupee cost averaging mutual fund",
    "பணவீக்கம்": "inflation purchasing power CPI real return compounding",
    "கூட்டு வட்டி": "compound interest compounding wealth exponential growth",
    "மத்திய அரசு பத்திரம்": "government securities G-Sec treasury bills SGB RBI retail direct",
    "தங்கப் பத்திரம்": "sovereign gold bond SGB RBI gold tax free",
    "म्यूचुअल फंड": "mutual fund SIP NAV equity debt index fund AMC",
    "एसआईपी": "SIP systematic investment plan rupee cost averaging",
    "मुद्रास्फीति": "inflation purchasing power CPI real return compounding",
    "चक्रवृद्धि ब्याज": "compound interest compounding wealth exponential growth",
    "सरकारी सिक्योरिटीज": "government securities G-Sec treasury bills SGB",
    "सॉवरेन गोल्ड बॉन्ड": "sovereign gold bond SGB RBI gold tax free",
    "మ్యూచువల్ ఫండ్స్": "mutual fund SIP NAV equity debt index",
    "సిప్": "SIP systematic investment plan rupee cost averaging",
    "ద్రవ్యోల్బణం": "inflation purchasing power real return",
    "ಮ್ಯೂಚುವಲ್ ಫಂಡ್": "mutual fund SIP NAV equity debt index",
    "ಸಿಪ್": "SIP systematic investment plan rupee cost averaging",
    "ಹಣದುಬ್ಬರ": "inflation purchasing power real return",
    "മ്യൂച്വൽ ഫണ്ട്": "mutual fund SIP NAV equity debt index",
    "എസ്ഐപി": "SIP systematic investment plan rupee cost averaging",
    "നാണയപ്പെരുപ്പം": "inflation purchasing power real return",

    # Personal Finance
    "பட்ஜெட்": "budget budgeting 50 30 20 rule savings expense planning",
    "வரவு செலவு": "budget budgeting expenses savings personal finance",
    "அவசர கால நிதி": "emergency fund contingency rainy day liquid savings FD",
    "बजट": "budget budgeting 50 30 20 rule savings expense planning",
    "आपातकालीन फंड": "emergency fund contingency rainy day liquid savings FD",
    "బడ్జెట్": "budget budgeting 50 30 20 rule savings expenses",
    "ఎమర్జెన్సీ ఫండ్": "emergency fund contingency rainy day liquid savings",
    "ಬಜೆಟ್": "budget budgeting 50 30 20 rule savings expenses",
    "ತುರ್ತು ನಿಧಿ": "emergency fund contingency rainy day liquid savings",
    "ബജറ്റ്": "budget budgeting 50 30 20 rule savings expenses",
    "അടിയന്തര ഫണ്ട്": "emergency fund contingency rainy day liquid savings",

    # Digital Security & Cyber Fraud
    "ஃபிஷிங்": "phishing fake customer care impersonation malicious link scam",
    "ஓடிபி": "OTP one time password credential theft SIM swap",
    "சிம் ஸ்வாப்": "SIM swap fraud mobile network duplicate SIM",
    "சைபர் கிரைம்": "cybercrime helpline 1930 CFCFRMS reporting portal",
    "फ़िशिंग": "phishing fake customer care impersonation malicious link scam",
    "ओटीपी": "OTP one time password credential theft SIM swap",
    "सिम स्वैप": "SIM swap fraud mobile network duplicate SIM",
    "साइबर हेल्पलाइन": "cybercrime helpline 1930 CFCFRMS reporting portal",

    # Insurance - Tamil (தமிழ்)
    "காப்பீடு": "insurance policy cover sum insured",
    "காத்திருப்பு": "waiting period PED pre-existing disease initial waiting",
    "காத்திருப்பு காலம்": "waiting period PED pre-existing disease initial waiting",
    "முன்பிருந்த நோய்": "pre-existing disease PED diabetes hypertension illness",
    "பணமில்லா சிகிச்சை": "cashless treatment network hospital TPA pre-authorization",
    "கேஷ்லெஸ்": "cashless hospital network TPA",
    "அறை வாடகை": "room rent limit icu capping sub-limit proportionate deduction",
    "அறை வாடகை வரம்பு": "room rent limit icu capping sub-limit proportionate deduction",
    "வான்வழி ஆம்புலன்ஸ்": "air ambulance emergency hospitalisation 250000 rider",
    "ஆம்புலன்ஸ்": "air ambulance emergency hospitalisation 250000 rider",
    "ரோபோடிக்": "robotic surgery modern treatments co-payment 10 percent",
    "உரிமைகோரல்": "claim settlement reimbursement cashless TPA documents",
    "உரிமைகோருதல்": "claim settlement reimbursement cashless TPA documents",
    "கிளைம்": "claim settlement reimbursement cashless TPA documents",
    "மருத்துவ": "health medical hospitalization disease illness cashless",
    "ஹெல்த்": "health medical hospitalization disease illness",
    "ஜீரோ டெப்ரிசியேஷன்": "zero depreciation bumper to bumper nil dep motor",
    "டேர்ம்": "term insurance life cover sum assured death benefit nominee",
    "நாமினி": "nominee beneficial nominee section 39 beneficiary",
    "ஒம்புட்ஸ்மேன்": "ombudsman insurance ombudsman grievance dispute IRDAI",
    "பயண காப்பீடு": "travel insurance international flight delay baggage medical emergency",

    # Insurance - Hindi (हिन्दी)
    "बीमा": "insurance policy cover sum insured",
    "प्रतीक्षा अवधि": "waiting period PED pre-existing disease initial waiting",
    "प्रतीक्षा": "waiting period PED pre-existing disease",
    "पहले से मौजूद बीमारी": "pre-existing disease PED diabetes hypertension",
    "कैशलेस उपचार": "cashless treatment network hospital TPA pre-authorization",
    "कैशलेस": "cashless treatment network hospital TPA",
    "कमरा किराया": "room rent limit icu capping sub-limit proportionate deduction single private AC room",
    "कमरे का किराया": "room rent limit icu capping sub-limit proportionate deduction single private AC room",
    "कमरे के किराए": "room rent limit icu capping sub-limit proportionate deduction single private AC room",
    "हवाई एम्बुलेंस": "air ambulance emergency hospitalisation 250000 rider",
    "एम्बुलेंस": "air ambulance emergency hospitalisation 250000 rider",
    "रोबोटिक सर्जरी": "robotic modern treatments co-payment 10 percent",
    "दावा": "claim settlement reimbursement cashless TPA documents",
    "क्लेम": "claim settlement reimbursement cashless TPA documents",
    "स्वास्थ्य": "health medical hospitalization disease illness",
    "हेल्थ": "health medical hospitalization disease illness",
    "जीरो डेप्रिसिएशन": "zero depreciation bumper to bumper nil dep motor",
    "टर्म इंश्योरेंस": "term insurance life cover sum assured death benefit nominee",
    "नॉमिनी": "nominee beneficial nominee section 39 beneficiary",
    "बीमा लोकपाल": "insurance ombudsman grievance dispute IRDAI bima bharosa",
    "यात्रा बीमा": "travel insurance international flight delay baggage medical emergency",

    # Insurance - Telugu (తెలుగు)
    "ఆరోగ్య బీమా": "health medical hospitalization cashless disease",
    "ఆరోగ్య": "health medical hospitalization",
    "బీమా": "insurance policy cover sum insured",
    "వేచి ఉండే సమయం": "waiting period PED pre-existing disease",
    "వేచి ఉండే కాలం": "waiting period PED pre-existing disease",
    "ముందున్న వ్యాధి": "pre-existing disease PED",
    "క్యాష్‌లెస్": "cashless treatment network hospital TPA",
    "గది అద్దె": "room rent limit icu capping sub-limit single private AC room",
    "ఎయిర్ అంబులెన్స్": "air ambulance emergency hospitalisation 250000 rider",
    "రోబోటిక్ సర్జరీ": "robotic modern treatments co-payment 10 percent",
    "రోబోటిక్": "robotic modern treatments co-payment 10 percent",
    "కో-పేమెంట్": "co-payment copay 10 percent",
    "క్లెయిమ్": "claim settlement reimbursement",
    "టర్మ్ இன்சூరెన్స్": "term insurance life cover nominee",
    "నామినీ": "nominee beneficial nominee section 39",
    "అంబుడ్స్‌మన్": "insurance ombudsman grievance dispute",

    # Insurance - Kannada (ಕನ್ನಡ)
    "ಆರೋಗ್ಯ ವಿಮೆ": "health medical hospitalization cashless disease",
    "ಆರೋಗ್ಯ": "health medical hospitalization",
    "ವಿಮೆ": "insurance policy cover sum insured",
    "ಕಾಯುವ ಅವಧಿ": "waiting period PED pre-existing disease 36 months",
    "ಮೊದಲೇ ಇರುವ ರೋಗ": "pre-existing disease PED 36 months",
    "ಮೊದಲೇ ಇರುವ ಕಾಯಿಲೆ": "pre-existing disease PED 36 months",
    "ಕ್ಯಾಶ್‌ಲೆಸ್": "cashless treatment network hospital TPA",
    "ಕೋಣೆ ಬಾಡಿಗೆ": "room rent limit icu capping sub-limit single private AC room",
    "ಏರ್ ಅಂಬ್ಯುಲೆನ್ಸ್": "air ambulance emergency hospitalisation 250000 rider",
    "ರೊಬೋಟಿಕ್ ಸರ್ಜರಿ": "robotic modern treatments co-payment 10 percent",
    "ಕ್ಲೈಮ್": "claim settlement reimbursement",
    "ಟರ್ಮ್ ಇನ್ಶೂರೆನ್ಸ್": "term insurance life cover nominee",
    "ನಾಮಿನಿ": "nominee beneficial nominee section 39",
    "ಲೋಕಪಾಲ": "insurance ombudsman grievance dispute",

    # Insurance - Malayalam (മലയാളം)
    "ആരോഗ്യ ഇൻഷുറൻസ്": "health medical hospitalization cashless disease",
    "ആരോഗ്യ": "health medical hospitalization",
    "ഇൻഷുറൻസ്": "insurance policy cover sum insured",
    "കാത്തിരിപ്പ് കാലാവധി": "waiting period PED pre-existing disease 36 months",
    "മുൻപുണ്ടായിരുന്ന രോഗം": "pre-existing disease PED 36 months",
    "ക്യാഷ്‌ലെസ്സ്": "cashless treatment network hospital TPA",
    "മുറി വാടക": "room rent limit icu capping sub-limit single private AC room",
    "എയർ ആംബുലൻസ്": "air ambulance emergency hospitalisation 250000 rider",
    "റോബോട്ടിക് സർജറി": "robotic modern treatments co-payment 10 percent",
    "ക്ലെയിം": "claim settlement reimbursement",
    "ടേം ഇൻഷുറൻസ്": "term insurance life cover nominee",
    "നോമിനി": "nominee beneficial nominee section 39",
    "ഓംബുഡ്സ്മാൻ": "insurance ombudsman grievance dispute",

    # Transliterated / Acronyms / Common financial terms
    "zero dep": "zero depreciation bumper to bumper nil dep",
    "copay": "co-payment copay cost sharing deduction",
    "ped": "pre-existing diseases PED waiting period",
    "tpa": "third party administrator cashless pre-authorization",
    "idv": "insured declared value market value vehicle depreciation",
    "ncb": "no claim bonus cumulative bonus transfer",
    "csr": "claim settlement ratio section 45 incontestability",
    "ombudsman": "insurance ombudsman banking ombudsman grievance dispute GRO bima bharosa",
    "eia": "electronic insurance account eIA insurance repository CAMSRep NDML",
    "cibil": "CIBIL credit score credit report bureau CICs",
    "sip": "SIP systematic investment plan rupee cost averaging mutual fund",
    "swp": "SWP systematic withdrawal plan mutual fund cash flow",
    "nav": "NAV net asset value mutual fund unit price",
    "ter": "TER total expense ratio direct plan regular plan",
    "g-sec": "government securities G-Sec treasury bills RBI retail direct",
    "sgb": "sovereign gold bond SGB gold 2.5 percent tax free",
    "fd": "fixed deposit FD term deposit interest DICGC",
    "rd": "recurring deposit RD monthly installment tenure",
    "bsbda": "BSBDA basic savings bank deposit account zero balance",
    "foir": "FOIR fixed obligation to income ratio loan eligibility",
    "ltv": "LTV loan to value ratio home loan down payment",
    "apr": "APR annual percentage rate credit card revolving interest",
    "mad": "MAD minimum amount due credit card interest trap",
    "cur": "CUR credit utilisation ratio credit score 30 percent",
    "buds": "BUDS Act banning unregulated deposit schemes Ponzi scam"
}

class InsuranceRAGRetriever:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or DEFAULT_HYBRID_CONFIG.copy()
        self.documents: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.doc_vectors = None
        self.doc_texts: List[str] = []
        self._initialize_index()

    def _initialize_index(self):
        """Load knowledge base documents and build TF-IDF index with field weighting."""
        self.documents = load_all_knowledge_documents()
        if not self.documents:
            print("[RAG] Warning: No documents found in knowledge base!")
            return

        self.doc_texts = []
        for doc in self.documents:
            # Weighted multi-field text representation:
            # Questions (x3), Title (x3), Keywords (x3), Category (x2), Subcategory (x2), Content (x1)
            title = doc.get("title", "")
            category = doc.get("category", "")
            subcategory = doc.get("subcategory", "")
            keywords = " ".join(doc.get("keywords", []))
            questions = " ".join(doc.get("questions", []))
            content = doc.get("content", "")

            weighted_text = (
                f"{category} {category} "
                f"{subcategory} {subcategory} "
                f"{title} {title} {title} "
                f"{keywords} {keywords} {keywords} "
                f"{questions} {questions} {questions} "
                f"{content}"
            ).lower()

            self.doc_texts.append(weighted_text)

        # Build sublinear TF-IDF vectorizer with (1, 2) word n-grams
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words='english',
            min_df=1
        )
        self.doc_vectors = self.vectorizer.fit_transform(self.doc_texts)
        print(f"[RAG] Successfully indexed {len(self.documents)} rich insurance knowledge chunks.")

    def _expand_query(self, query: str) -> str:
        """Expand Indic queries with domain concepts for cross-lingual matching."""
        expanded_tokens = [query]
        q_lower = query.lower()
        for indic_term, expansion in INDIC_CONCEPT_SYNONYMS.items():
            if indic_term in q_lower:
                expanded_tokens.append(expansion)
        return " ".join(expanded_tokens)

    def _extract_distinctive_tokens(self, query: str) -> List[str]:
        """Extract meaningful non-generic words from query, including 2-letter financial acronyms."""
        tokens = re.findall(r'[\w\-]+', query.lower())
        ALLOWED_SHORT_TOKENS = {"fd", "rd", "si", "ci", "qr"}
        distinctive = [t for t in tokens if (len(t) > 2 or t in ALLOWED_SHORT_TOKENS) and t not in DOMAIN_GENERIC_WORDS]
        return distinctive

    def _compute_keyword_score(self, doc: Dict[str, Any], query: str, distinctive_tokens: List[str]) -> float:
        """
        Compute high-precision keyword overlap score.
        Gives heavy weight to title matches, explicit keyword list matches, questions, and subcategories.
        """
        if not distinctive_tokens:
            return 0.0

        title_lower = doc.get("title", "").lower()
        subcategory_lower = doc.get("subcategory", "").lower()
        keywords_lower = [k.lower() for k in doc.get("keywords", [])]
        questions_lower = [q.lower() for q in doc.get("questions", [])]
        content_lower = doc.get("content", "").lower()

        distinctive_set = set(distinctive_tokens)
        q_lower = query.lower()

        # 1. Exact phrase matching in title, subcategory, or questions
        phrase_hits = 0
        if len(distinctive_tokens) >= 2:
            query_phrase = " ".join(distinctive_tokens[:3])
            if query_phrase in title_lower or query_phrase in subcategory_lower or any(query_phrase in q for q in questions_lower):
                phrase_hits += 2.0

        # 2. Token overlap across fields
        title_words = set(re.findall(r'[\w\-]+', title_lower))
        subcategory_words = set(re.findall(r'[\w\-]+', subcategory_lower))
        keyword_words = set(re.findall(r'[\w\-]+', " ".join(keywords_lower)))
        question_words = set(re.findall(r'[\w\-]+', " ".join(questions_lower)))

        title_overlap = len(distinctive_set.intersection(title_words))
        subcat_overlap = len(distinctive_set.intersection(subcategory_words))
        keyword_overlap = len(distinctive_set.intersection(keyword_words))
        question_overlap = len(distinctive_set.intersection(question_words))

        # 3. High-priority exact acronym boost
        acronym_boost = 0.0
        for acr in ["fd", "rd", "sip", "swp", "emi", "cibil", "upi", "kyc", "eia", "sgb", "1930", "amb", "bsbda", "mad", "cur", "buds"]:
            if acr in distinctive_set and (acr in title_words or acr in keyword_words or acr in subcategory_words):
                acronym_boost += 0.35

        # Check content overlap
        content_words = set(re.findall(r'[\w\-]+', content_lower))
        content_overlap = len(distinctive_set.intersection(content_words))

        score = (
            (title_overlap * 0.35) +
            (subcat_overlap * 0.20) +
            (keyword_overlap * 0.30) +
            (question_overlap * 0.25) +
            (phrase_hits * 0.40) +
            acronym_boost +
            (min(3, content_overlap) * 0.08)
        )

        # Normalize score to [0, 1] range
        normalized = min(1.0, score / max(1.0, len(distinctive_set) * 0.5))
        return round(normalized, 3)

    def _compute_semantic_score(self, doc: Dict[str, Any], query: str, expanded_query: str) -> float:
        """
        Lightweight semantic overlap score based on character & token subword similarity
        against target query questions, titles, and subcategories.
        """
        questions = doc.get("questions", [])
        title = doc.get("title", "")
        subcategory = doc.get("subcategory", "")
        targets = [title, subcategory] + questions

        q_tokens = set(re.findall(r'\w+', expanded_query.lower()))
        if not q_tokens:
            return 0.0

        best_jaccard = 0.0
        for target in targets:
            t_tokens = set(re.findall(r'\w+', target.lower()))
            if not t_tokens:
                continue
            intersection = len(q_tokens.intersection(t_tokens))
            union = len(q_tokens.union(t_tokens))
            jaccard = intersection / union if union > 0 else 0.0
            if jaccard > best_jaccard:
                best_jaccard = jaccard

        # Character tri-gram overlap for subword and morphological similarity
        def get_trigrams(s: str) -> set:
            s = f"^{s.lower()}$"
            return set(s[i:i+3] for i in range(len(s)-2))

        q_tri = get_trigrams(query)
        best_char_sim = 0.0
        for target in targets:
            t_tri = get_trigrams(target)
            if not t_tri:
                continue
            tri_sim = len(q_tri.intersection(t_tri)) / len(q_tri.union(t_tri)) if q_tri.union(t_tri) else 0.0
            if tri_sim > best_char_sim:
                best_char_sim = tri_sim

        semantic_score = (best_jaccard * 0.65) + (best_char_sim * 0.35)
        return round(min(1.0, semantic_score * 1.8), 3)

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[RAGSource]:
        """
        Retrieve relevant knowledge base chunks using Hybrid Ranking + Dynamic Relevance Threshold.
        DOES NOT FORCE TOP 3: Returns 0, 1, 2, or up to top_k results based on relevance.
        """
        if not self.documents or not self.vectorizer or not query.strip():
            return []

        max_k = top_k or self.config["max_top_k"]
        min_threshold = self.config["min_relevance_threshold"]

        expanded_query = self._expand_query(query)
        distinctive_tokens = self._extract_distinctive_tokens(query)

        # Compute TF-IDF Cosine Similarity
        query_vec = self.vectorizer.transform([expanded_query.lower()])
        tfidf_similarities = cosine_similarity(query_vec, self.doc_vectors)[0]

        # Domain generic query check: if query has NO distinctive terms, penalize TF-IDF
        is_generic_query = len(distinctive_tokens) == 0

        # Specific intent disambiguation flags
        q_lower = query.lower()
        q_tokens_set = set(re.findall(r'[\w\-]+', q_lower))

        is_ped_query = any(k in q_lower for k in ["pre-existing", "pre existing", "முன்பிருந்த", "पहले से मौजूद"]) or "ped" in q_tokens_set
        is_maternity_query = any(k in q_lower for k in ["maternity", "pregnancy", "delivery", "newborn", "மகப்பேறு", "गर्भावस्था", "प्रसव"])
        is_cashless_query = any(k in q_lower for k in ["cashless", "network hospital", "reimbursement", "பணமில்லா", "கேஷ்லெஸ்", "कैशलेस"]) or "tpa" in q_tokens_set
        is_upi_query = any(k in q_lower for k in ["unified payments interface", "npci", "vpa", "யுபிஐ", "यूपीआई", "autopay"]) or "upi" in q_tokens_set
        is_fd_rd_query = any(k in q_lower for k in ["fixed deposit", "recurring deposit", "பிக்சட் டெபாசிட்", "தொடர் வைப்பு", "फिक्स्ड डिपॉजिट", "आवर्ती जमा", "dicgc"]) or bool(q_tokens_set & {"fd", "rd"})
        is_savings_current_query = any(k in q_lower for k in ["savings account", "current account", "சேமிப்பு கணக்கு", "நடப்பு கணக்கு", "बचत खाता", "चालू खाता"])
        is_loan_emi_query = any(k in q_lower for k in ["amortisation", "equated monthly", "reducing balance", "flat interest", "இஎம்ஐ", "ईएमआई", "मासिक किस्त"]) or "emi" in q_tokens_set
        is_credit_score_query = any(k in q_lower for k in ["credit score", "credit rating", "experian", "equifax", "சிபில்", "கிரெடிட் ஸ்கோர்", "सिबिल", "क्रेडिट स्कोर"]) or "cibil" in q_tokens_set
        is_sip_query = any(k in q_lower for k in ["systematic investment plan", "rupee cost averaging", "எஸ்ஐபி", "एसआईपी"]) or bool(q_tokens_set & {"sip", "swp"})
        is_budget_query = any(k in q_lower for k in ["50/30/20", "50 30 20", "budgeting", "budget", "பட்ஜெட்", "बजट"])
        is_emergency_fund_query = any(k in q_lower for k in ["emergency fund", "contingency fund", "rainy day fund", "அவசர கால நிதி", "आपातकालीन फंड"])
        is_fraud_helpline_query = any(k in q_lower for k in ["helpline 1930", "cybercrime.gov.in", "cfcfrms", "சைபர் கிரைம்", "1930 हेल्पलाइन"]) or "1930" in q_tokens_set
        is_qr_scam_query = any(k in q_lower for k in ["qr code scam", "collect request", "scan to receive", "qr scam"])
        is_eia_query = any(k in q_lower for k in ["electronic insurance account", "insurance repository", "camsrep", "ndml"]) or "eia" in q_tokens_set

        is_failed_txn_query = any(k in q_lower for k in ["failed", "pending", "debited but", "t+1", "reversal"]) or "tat" in q_tokens_set
        is_nominee_bank_query = any(k in q_lower for k in ["nominee", "nomination", "நாமினி", "नॉमिनी"]) and any(k in q_lower for k in ["bank", "savings", "account", "வங்கி", "खाता"])
        is_card_liability_query = any(k in q_lower for k in ["unauthorized", "3 days", "card fraud", "debit vs credit", "debit card"]) or ("liability" in q_lower and "card" in q_lower)
        is_credit_dispute_query = any(k in q_lower for k in ["dispute", "erroneous", "error", "unknown loan", "30 days"]) and any(k in q_lower for k in ["cibil", "credit", "report", "சிபில்"])
        is_rtgs_neft_query = any(k in q_lower for k in ["rtgs", "neft", "imps", "gross settlement", "2 lakh", "2,00,000"])
        is_tax_query = any(k in q_lower for k in ["80c", "80d", "section 80", "tax deduction", "income tax", "tax benefits"])
        is_third_party_motor_query = any(k in q_lower for k in ["third party", "third-party", "comprehensive", "own damage", "zero dep", "zero depreciation"]) and any(k in q_lower for k in ["motor", "car", "bike", "vehicle", "insurance"])

        candidates: List[RAGSource] = []
        for idx, doc in enumerate(self.documents):
            raw_tfidf = float(tfidf_similarities[idx])
            
            # Penalize generic queries so they don't match arbitrary documents
            tfidf_score = raw_tfidf * 0.35 if is_generic_query else raw_tfidf

            # Keyword and Semantic scores
            keyword_score = self._compute_keyword_score(doc, query, distinctive_tokens)
            semantic_score = self._compute_semantic_score(doc, query, expanded_query)

            # Combined Hybrid Score
            w_tfidf = self.config["weight_tfidf"]
            w_semantic = self.config["weight_semantic"]
            w_keyword = self.config["weight_keyword"]

            final_score = (
                w_tfidf * tfidf_score +
                w_semantic * semantic_score +
                w_keyword * keyword_score
            )

            # Subtopic intent adjustments:
            doc_id = doc.get("id", "")
            doc_title_lower = doc.get("title", "").lower()

            # 1. PED vs Maternity Disambiguation
            if is_ped_query and not is_maternity_query:
                # If query specifically asks about PED, heavily penalize maternity chunks and boost PED chunk
                if doc_id == "health-06" or "maternity" in doc_title_lower:
                    final_score *= 0.15
                elif doc_id == "health-02" or ("waiting period" in doc_title_lower and "pre-existing" in doc_title_lower):
                    final_score = min(1.0, final_score + 0.50)
            elif is_maternity_query and not is_ped_query:
                # If query asks about maternity, penalize general PED chunk
                if doc_id == "health-02" and "maternity" not in doc_title_lower:
                    final_score *= 0.30

            # 2. Cashless Claim Intent
            if is_cashless_query:
                if doc_id == "health-05" or "cashless" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.35)

            # 3. Failed Transaction & Reversal Intent
            if is_failed_txn_query:
                if doc_id == "fintech-05" or "failed transaction" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.45)

            # 4. UPI & Fintech Intent (general)
            elif is_upi_query:
                if doc_id in ("fintech-01", "fintech-02") or "upi" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.40)

            # 5. Bank Account Nomination Intent
            if is_nominee_bank_query:
                if doc_id == "bank-04" or "nomination" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.45)

            # 6. Card Fraud & Zero Liability Intent
            if is_card_liability_query:
                if doc_id == "cred-05" or "liability" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.45)

            # 7. Credit Report Dispute Intent
            if is_credit_dispute_query:
                if doc_id == "cred-06" or "credit report error" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.50)

            # 8. Banking FD / RD Intent
            if is_fd_rd_query:
                if doc_id == "bank-02" or "fixed deposit" in doc_title_lower or "recurring deposit" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.45)

            # 9. Savings vs Current Account Intent
            if is_savings_current_query and not is_nominee_bank_query:
                if doc_id == "bank-01" or "savings account" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.45)

            # 10. EMI & Amortisation Intent
            if is_loan_emi_query:
                if doc_id == "loan-02" or "equated monthly instalment" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.45)

            # 11. Credit Score / CIBIL Intent
            if is_credit_score_query and not is_credit_dispute_query:
                if doc_id in ("cred-01", "cred-02") or "credit score" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.45)

            # 12. SIP / SWP Intent
            if is_sip_query:
                if doc_id == "inv-02" or "systematic investment plan" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.45)

            # 13. Budgeting 50/30/20 Intent
            if is_budget_query:
                if doc_id == "pf-01" or "50/30/20" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.45)

            # 14. Emergency Fund Intent
            if is_emergency_fund_query:
                if doc_id == "pf-02" or "emergency fund" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.45)

            # 15. Cyber Helpline 1930 Intent
            if is_fraud_helpline_query:
                if doc_id == "sec-06" or "1930" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.45)

            # 16. QR Code Scam Intent
            if is_qr_scam_query:
                if doc_id == "sec-02" or "qr code" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.45)

            # 17. e-Insurance Account Intent
            if is_eia_query:
                if doc_id == "insfin-02" or "electronic insurance account" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.45)

            # 18. RTGS / NEFT / IMPS Large Value Transfers Intent
            if is_rtgs_neft_query:
                if doc_id in ("fintech-03", "rtgs_large_value_transfer") or "rtgs" in doc_title_lower or "neft" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.50)

            # 19. Section 80C & 80D Tax Benefits Intent
            if is_tax_query:
                if doc_id == "terms-02" or "80d" in doc_title_lower or "80c" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.50)

            # 20. Motor Insurance (Third-Party vs Comprehensive) Intent
            if is_third_party_motor_query:
                if doc_id in ("motor-01", "motor-02") or "third-party" in doc_title_lower or "comprehensive" in doc_title_lower:
                    final_score = min(1.0, final_score + 0.50)

            # Cap score between 0.0 and 1.0
            final_score = round(min(1.0, max(0.0, final_score)), 3)

            # Strict relevance threshold filtering (DO NOT FORCE TOP 3)
            if final_score >= min_threshold:
                snippet = doc.get("content", "")
                if len(snippet) > 280:
                    snippet = snippet[:280] + "..."

                candidates.append(RAGSource(
                    id=doc.get("id", f"kb-{idx}"),
                    category=doc.get("category", "General Insurance"),
                    title=doc.get("title", "Insurance Policy Information"),
                    snippet=snippet,
                    relevance_score=final_score,
                    source_type="knowledge_base",
                    tfidf_score=round(tfidf_score, 3),
                    keyword_score=round(keyword_score, 3),
                    semantic_score=round(semantic_score, 3)
                ))

        # Sort candidates descending by relevance score
        candidates.sort(key=lambda s: s.relevance_score, reverse=True)

        if not candidates:
            return []

        # Relative Margin Pruning: Do NOT blindly include multiple chunks if top chunk is decisive
        top_score = candidates[0].relevance_score
        pruned_candidates: List[RAGSource] = [candidates[0]]

        for cand in candidates[1:]:
            # If top chunk is highly authoritative (>= 0.55), only accept secondary chunks
            # that are closely clustered (within 0.16) and genuinely relevant (>= 0.45)
            if top_score >= 0.55:
                if cand.relevance_score >= 0.45 and (top_score - cand.relevance_score) <= 0.16:
                    pruned_candidates.append(cand)
            else:
                # For moderate top scores, require at least 0.35 and within 0.12 of top score
                if cand.relevance_score >= 0.35 and (top_score - cand.relevance_score) <= 0.12:
                    pruned_candidates.append(cand)

            if len(pruned_candidates) >= max_k:
                break

        return pruned_candidates

    def retrieve_multi_source(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[RAGSource]:
        """
        Multi-Source RAG Retrieval Strategy:
        1. If an uploaded document is active for the session, search the uploaded document.
        2. Search the existing insurance knowledge base.
        3. Prioritize uploaded document sources when query relates to uploaded policy.
        4. Apply relative margin pruning to prevent topic confusion.
        """
        from backend.services.rag.document_retriever import document_retriever

        max_k = top_k or self.config["max_top_k"]

        # If no active uploaded document in session, fall back directly to base knowledge base
        if not session_id or not document_retriever.has_document(session_id):
            return self.retrieve(query=query, top_k=max_k)

        # 1. Search uploaded document
        doc_sources = document_retriever.retrieve(
            session_id=session_id,
            query=query,
            top_k=max_k,
            min_threshold=self.config["min_relevance_threshold"]
        )

        # 2. Search base insurance knowledge base
        kb_sources = self.retrieve(query=query, top_k=max_k)

        # Check if query refers specifically to the uploaded policy or document
        q_lower = query.lower()
        doc_info = document_retriever.get_document_info(session_id)
        doc_name_lower = (doc_info["document_name"] if doc_info else "").lower()

        asks_about_doc = any(k in q_lower for k in [
            "uploaded", "my policy", "my document", "this policy", "arogya", "sanjeevani", "clause", "page",
            "in this document", "as per document", "as per policy", "under this policy", "schedule", "this cover"
        ]) or bool(doc_name_lower and any(w in q_lower for w in doc_name_lower.replace(".pdf","").replace(".docx","").replace(".txt","").split("_") if len(w) > 3))

        # 1. If uploaded document has matching chunks:
        if doc_sources:
            if asks_about_doc or doc_sources[0].relevance_score >= 0.30:
                # Strictly prioritize document chunks and do NOT inject unrelated base KB chunks
                return doc_sources[:max_k]

        # 2. If user specifically asks about the uploaded document, never substitute general KB
        if asks_about_doc:
            return doc_sources[:max_k]

        # 3. If doc sources did not match well but general insurance query was asked, return base KB
        if kb_sources and (not doc_sources or kb_sources[0].relevance_score > doc_sources[0].relevance_score + 0.15):
            return kb_sources[:max_k]

        return (doc_sources + kb_sources)[:max_k]

    def get_context_text(self, sources: List[RAGSource]) -> str:
        """Format retrieved sources into context text for the LLM prompt."""
        if not sources:
            return "No specific documents found in knowledge base."

        context_parts = []
        for i, src in enumerate(sources, 1):
            if src.source_type == "uploaded_document":
                page_info = f" (Page {src.page})" if src.page else ""
                heading_info = f" - Section: \"{src.section_heading}\"" if src.section_heading else ""
                context_parts.append(f"[Uploaded Document #{i}: {src.document_name}{page_info}{heading_info}]\n{src.snippet}")
            else:
                context_parts.append(f"[IRDAI Knowledge Base #{i} - {src.category}: {src.title}]\n{src.snippet}")
        return "\n\n".join(context_parts)

# Singleton instance
rag_retriever = InsuranceRAGRetriever()
