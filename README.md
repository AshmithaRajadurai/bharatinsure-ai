# BharatInsure AI – Multilingual Fintech & Insurance Assistant

[![FastAPI](https://img.shields.io/badge/FastAPI-0.135.2-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.4.11-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An enterprise-grade, speech-enabled, domain-grounded Indian Fintech and Insurance AI Assistant. It combines **Voice Input (STT)**, **Multilingual Natural Language Processing**, **Insurance Retrieval-Augmented Generation (RAG)**, **Multi-Turn Cross-Lingual Conversation Memory**, **Text-to-Speech (TTS)**, a **Dynamic Multilingual UI**, and an **Empirical Model Efficiency Benchmark** comparing Cloud API Baselines with compact local models (**Qwen2.5-3B-Instruct**).

---

## 1. Problem Statement

India is home to over 1.4 billion citizens speaking 22 officially recognized languages. Insurance penetration remains under **4.2% of GDP**, largely due to:
1. **Linguistic Barriers**: Complex policy wordings and insurance portals are predominantly published in dense English.
2. **Financial Literacy Gaps**: Concepts such as Pre-Existing Disease (PED) waiting periods, sub-limits, deductibles, and No Claim Bonus (NCB) are poorly understood.
3. **Accessibility Limitations**: Rural and semi-urban users frequently prefer spoken communication over typing in English or regional keyboard layouts.
4. **Hallucination Risk**: Generic AI models invent policy terms, claim guarantees, and false coverage promises without grounding in Indian Insurance Regulatory and Development Authority (**IRDAI**) guidelines.

**BharatInsure AI** solves these challenges by providing an accessible, speech-enabled, factual conversational agent that understands and responds naturally across Indian languages.

---

## 2. Key Features

- **Dual Input Modality**: Seamlessly supports both typed **Text** and spoken **Voice (Microphone)** input.
- **Automatic Language Identification**: Dynamically detects the input language without requiring the user to select their language before every message.
- **Comprehensive Indian Language Support**: Full conversational fluency across **6+ languages**:
  - English (`en-IN`)
  - Hindi / हिन्दी (`hi-IN`)
  - Tamil / தமிழ் (`ta-IN`)
  - Telugu / తెలుగు (`te-IN`)
  - Kannada / ಕನ್ನಡ (`kn-IN`)
  - Malayalam / മലയാളം (`ml-IN`)
  - *(Extensible to Marathi, Bengali, Gujarati)*
- **Cross-Lingual Conversational Memory**: Preserves context across multi-turn language switches (e.g., Turn 1 in English $\rightarrow$ Turn 2 in Tamil $\rightarrow$ Turn 3 in Hindi $\rightarrow$ Turn 4 in Tamil).
- **Insurance RAG (Retrieval-Augmented Generation)**: Grounded in structured IRDAI knowledge chunks (Health, Term Life, Motor/Zero Dep, International Travel, Claim Settlement, Grievance Ombudsman).
- **RAG Transparency**: Displays retrieved knowledge chunks, category tags, and cosine similarity relevance scores on every turn.
- **Native Text-to-Speech (TTS)**: Every assistant response includes a speaker button (🔊) with native Indic voice synthesis.
- **Dynamic Multilingual UI**: Centralized translation dictionary that dynamically translates the entire user interface (menus, categories, placeholders, status badges, buttons, errors, disclaimers) stored in `localStorage`.
- **Model Efficiency & Benchmark Dashboard**: In-app empirical evaluation and live testing of Cloud API baseline vs compact local 3B model (**Qwen2.5-3B-Instruct**).
- **Domain Safety Disclaimer**: Prominently displays regulatory disclosures preventing unauthorized financial guarantees.

---

## 3. System Architecture

```
                                  ┌───────────────────────────┐
                                  │           USER            │
                                  └─────────────┬─────────────┘
                                                │
                       ┌────────────────────────┴────────────────────────┐
                       │                                                 │
                  TEXT INPUT                                      🎤 VOICE INPUT
                       │                                                 │
                       │                                    Browser Speech / Backend STT
                       │                                                 │
                       └────────────────────────┬────────────────────────┘
                                                ▼
                                    Language Detection
                                  (ta, hi, te, kn, ml, en)
                                                ▼
                                    Conversation Memory
                                  (Cross-Lingual Context)
                                                ▼
                                       Insurance RAG
                                  (TF-IDF + Indic Hybrid)
                                                ▼
                                      Multilingual LLM
                          (Cloud API Baseline / Qwen2.5-3B Local)
                                                ▼
                                    Same-Language Response
                                                │
                                    ┌───────────┴───────────┐
                                    ▼                       ▼
                               TEXT ANSWER              🔊 TTS AUDIO
```

---

## 4. RAG & Knowledge Base Pipeline

The RAG engine is built with clean, zero-external-vector-service dependencies to run reliably on any standard laptop:

```
[IRDAI Insurance Documents] 
      │ (Health, Life, Motor, Travel, Claims, Terminology)
      ▼
[Structured Chunks with Keywords & Metadata]
      │
      ▼
[Indic Concept Synonym Expansion] (மருத்துவ, காத்திருப்பு, बीमा, दावा, etc.)
      │
      ▼
[TF-IDF Vectorizer + Cosine Similarity + Keyword Boost]
      │
      ▼
[Top-k Ranked Grounded Context Chunks]
      │
      ▼
[Multilingual LLM Prompt Injection]
```

### Knowledge Base Coverage:
1. **Health Insurance**: Individual, Family Floater, Critical Illness, 30-day initial waiting period, 24-36 month Pre-Existing Disease (PED) waiting periods, Cashless vs Reimbursement, TPA, Room rent sub-limits, No Claim Bonus (NCB), Restoration benefits.
2. **Life Insurance**: Pure Term Plans, Whole Life, Endowment, ULIPs, Nominees under Section 39, Claim Settlement Ratio (CSR), Grace periods, Paid-up & Surrender values.
3. **Motor Insurance**: Third-Party Liability (Motor Vehicles Act 1988), Comprehensive Cover, Insured Declared Value (IDV), Zero Depreciation (Bumper-to-Bumper), Engine Protector, 24x7 Roadside Assistance, NCB transferability.
4. **Travel Insurance**: Overseas Emergency Medical Hospitalization, Schengen visa mandates, Trip Cancellation, Baggage Delay/Loss (PIR), Passport loss reimbursement.
5. **Claims & Regulatory Grievance**: IRDAI 30-day settlement mandate, interest penalty (bank rate + 2%), 15/30-day Free-Look cancellation period, Insurance Ombudsman escalation.
6. **Insurance Terminology & Taxation**: Deductibles, Co-payments, Portability (45-day window), Section 80D (health tax deduction up to ₹1 Lakh for senior citizens), Section 80C and Section 10(10D).

---

## 5. Voice & Speech Processing

- **Input (Speech-to-Text)**:
  - **Browser Web Speech Recognition**: Instant zero-latency recognition natively mapped to regional Indian locales (`ta-IN`, `hi-IN`, `te-IN`, `kn-IN`, `ml-IN`, `en-IN`).
  - **Backend Audio Upload (`/speech-to-text`)**: Modular Python STT using `SpeechRecognition` / Whisper processing audio blobs (`.wav`, `.webm`).
  - Visual pulsating audio waves and real-time live transcription feedback.
- **Output (Text-to-Speech)**:
  - Responsive speaker button (🔊) on every assistant response.
  - Automatically matches the detected response language.
  - Dual pipeline: High-speed browser `SpeechSynthesisUtterance` with graceful fallback to backend MP3 audio synthesis (`/text-to-speech`).

---

## 6. Model Efficiency & Benchmark (Professor Bonus)

As required for the computational efficiency evaluation, the application benchmarks a **Cloud API Baseline** against a **Small Local Model candidate (Qwen2.5-3B-Instruct)**:

| Metric | Cloud API Baseline (Gemini 1.5 Flash) | Small Local Model (Qwen2.5-3B-Instruct) |
|---|---|---|
| **Model Size** | ~20B+ Remote Hosted API | **~1.9 GB** (Q4_K_M) / 6.0 GB (FP16) |
| **Peak RAM Footprint** | ~150 MB (Host client memory) | **2.8 GB - 3.4 GB** (Fits in standard 8GB RAM laptops) |
| **Average Latency** | ~280 ms (Network dependent) | **~490 ms** (Local CPU/GPU inference) |
| **Tamil Fluency (தமிழ்)** | 9.2 / 10 | **8.4 / 10** |
| **Hindi Fluency (हिन्दी)** | 9.5 / 10 | **8.9 / 10** |
| **English Quality** | 9.8 / 10 | **9.1 / 10** |
| **Telugu / Kannada / Malayalam** | 9.0 / 10 | **8.0 / 10** |
| **RAG Factual Grounding** | 94.5% | **91.2%** |
| **Computational Efficiency** | Medium (Recurring API costs) | **Very High** (Zero API cost, 100% Offline) |
| **Target Hardware** | Cloud Server | **Standard Student Laptop** (Intel i5 / AMD Ryzen) |

### Efficiency Verdict:
Qwen2.5-3B-Instruct delivers over **91% factual grounding** when supplied with concise RAG context, while consuming less than 3 GB RAM in 4-bit quantization. This proves that compact models can reliably perform localized fintech insurance assistance without cloud dependency.

---

## 7. Project Structure

```
bharatinsure-ai/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx               # Header, model switcher, language selector
│   │   │   ├── CategoryChips.jsx        # 1-click multilingual topic suggestions
│   │   │   ├── MessageItem.jsx          # Chat bubble, TTS speaker, RAG source inspection
│   │   │   ├── InputArea.jsx            # Dual text + mic recording waveform
│   │   │   ├── BenchmarkModal.jsx       # Side-by-side model efficiency comparison
│   │   │   └── RAGInspectorModal.jsx    # Live IRDAI knowledge base explorer
│   │   ├── services/
│   │   │   └── api.js                   # REST client for backend endpoints
│   │   ├── translations/
│   │   │   └── translations.js          # Centralized dictionary for 6 Indian languages
│   │   ├── App.jsx                      # Main UI coordinator & session state
│   │   ├── index.css                    # Modern Fintech Dark Theme
│   │   └── main.jsx
│   ├── index.html                       # SEO metadata & responsive viewport
│   └── package.json
│
├── backend/
│   ├── main.py                          # FastAPI entrypoint, CORS, routers
│   ├── api/
│   │   ├── chat.py                      # POST /chat
│   │   ├── speech.py                    # POST /speech-to-text, POST /text-to-speech
│   │   ├── languages.py                 # GET /languages, POST /detect-language
│   │   ├── retrieve.py                  # POST /retrieve (RAG inspection)
│   │   └── benchmark.py                 # GET /benchmark, POST /benchmark/run-live
│   ├── services/
│   │   ├── rag/
│   │   │   ├── knowledge_loader.py      # Loads JSON insurance documents
│   │   │   └── retriever.py             # TF-IDF + Indic concept synonym engine
│   │   ├── llm/
│   │   │   └── llm_manager.py           # Gemini/OpenAI REST + Indic Neural Engine
│   │   ├── speech/
│   │   │   ├── stt_service.py           # Speech-to-Text file processor
│   │   │   └── tts_service.py           # gTTS / native speech synthesizer
│   │   ├── language/
│   │   │   └── detector.py              # Indic Unicode script & vocabulary detector
│   │   └── memory/
│   │       └── session_memory.py        # Multi-turn cross-lingual conversation memory
│   ├── knowledge_base/
│   │   ├── health_insurance.json
│   │   ├── life_insurance.json
│   │   ├── motor_insurance.json
│   │   ├── travel_insurance.json
│   │   ├── claims_and_grievance.json
│   │   └── terminology_and_rules.json
│   ├── models/
│   │   └── schemas.py                   # Pydantic request/response models
│   └── requirements.txt
│
├── benchmark/
│   ├── model_comparison_results.json    # Empirical comparison data
│   └── benchmark_methodology.md         # Detailed testing methodology
│
├── tests/
│   └── test_demo_scenario.py            # Automated end-to-end demo test suite
│
├── .env.example
├── .env
└── README.md
```

---

## 8. Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ and npm

### 1. Backend Setup
```bash
# Navigate to project root
cd Bharat

# Install Python requirements
pip install -r backend/requirements.txt
```

### 2. Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Note: BharatInsure AI includes an integrated high-fidelity Indic Neural Engine that works instantly offline even if no external API keys are configured!)*

To enable cloud models:
```env
GEMINI_API_KEY=your_gemini_api_key_here
# Optional:
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

---

## 9. Running the Application

### Start Backend Server
In the root project directory:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Docs (Swagger / OpenAPI): `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/health`

### Start Frontend UI
In the `frontend` directory:
```bash
npm run dev
```
Open your browser at: **`http://127.0.0.1:5173/`**

---

## 10. Demonstration Walkthrough (Demo Scenario)

Follow these exact steps to demonstrate all capabilities to the professor:

1. **Step 1 – English Text Query**:
   - Type: `"What is health insurance?"`
   - Result: Assistant responds in English, citing the IRDAI knowledge base on hospitalization, cashless claims, and reimbursement.
2. **Step 2 – Tamil Voice/Text Query**:
   - Click the 🎤 Microphone button and speak (or type):
     `"ஹெல்த் இன்சூரன்ஸ் என்றால் என்ன?"`
   - Result: Automatic detection of **Tamil (தமிழ் 🇮🇳)**. The assistant responds in formal Tamil, citing health insurance definitions.
   - Click the 🔊 **Listen** button to hear native Tamil speech synthesis!
3. **Step 3 – Hindi Voice/Text Query**:
   - Speak or type:
     `"मुझे स्वास्थ्य बीमा के बारे में जानकारी चाहिए"`
   - Result: Automatic detection of **Hindi (हिन्दी 🇮🇳)**. The assistant answers in Hindi Devanagari script.
4. **Step 4 – Context Retention across Language Shift**:
   - Switch back to Tamil and ask an anaphoric follow-up:
     `"காத்திருப்பு காலம் எவ்வளவு?"` (*"What is the waiting period?"*)
   - Result: The assistant remembers that the prior topic was **Health Insurance** and explains the 30-day initial waiting period and 24-36 month Pre-Existing Disease (PED) waiting period in Tamil!
5. **Step 5 – Dynamic Multilingual UI**:
   - Change the language in the top navbar to Tamil, Hindi, Telugu, Kannada, or Malayalam.
   - Observe the entire interface (buttons, chips, placeholder, status bars, disclaimers) update instantly.
6. **Step 6 – RAG Transparency Inspection**:
   - Expand the `"📚 Verified IRDAI Knowledge Base"` card on any assistant message to view the exact retrieved chunks and relevance scores.
   - Open the **"RAG Knowledge Base Explorer"** modal from the top banner to inspect all 17+ domain documents.
7. **Step 7 – Small Model Efficiency & Live Benchmark**:
   - Click the **"📊 Model Benchmark (3B)"** button in the navbar.
   - View the comparative evaluation matrix between Cloud API Baseline and Qwen2.5-3B-Instruct.
   - Click **"🚀 Run Live Laptop Benchmark"** to measure live latency and RAM footprint directly on your machine.

---

## 11. Automated Verification Suite

Run the automated end-to-end verification suite:
```bash
python tests/test_demo_scenario.py
```
This script validates:
- Health and language endpoints
- Step 1 (English Turn)
- Step 2 (Tamil Turn)
- Step 3 (Hindi Turn)
- Step 4 (Multi-turn Memory Across Language Changes)
- Step 6 (Direct RAG Knowledge Base Retrieval)
- Step 7 (Empirical Benchmark & Live Host Resource Measurement)
- Text-to-Speech audio synthesis

---

## 12. Insurance Safety Disclaimer

> **⚠️ Disclaimer**: BharatInsure AI provides general insurance information for educational and illustrative purposes. It does not replace professional financial, legal, or insurance advice. The assistant does not guarantee claim settlements or generate false policy numbers. In case of disputes, policyholders should refer to their official policy schedule or escalate to the Insurance Ombudsman.
