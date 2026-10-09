import React, { useState, useRef, useEffect } from "react";

// Exact 5 suggested questions per topic as specified
export const TOPICS_DATA = {
  health: {
    id: "health",
    title: "Health Insurance",
    icon: "🏥",
    questions: {
      en: [
        "What does health insurance cover?",
        "What is the difference between an initial waiting period and a PED waiting period?",
        "What are room-rent limits in health insurance?",
        "What is a co-payment in a health insurance policy?",
        "What documents are required to file a health insurance claim?"
      ],
      hi: [
        "स्वास्थ्य बीमा में क्या कवर होता है?",
        "शुरुआती प्रतीक्षा अवधि और PED प्रतीक्षा अवधि में क्या अंतर है?",
        "स्वास्थ्य बीमा में कमरे के किराए की सीमा (Room-rent limit) क्या है?",
        "स्वास्थ्य बीमा पॉलिसी में सह-भुगतान (Co-payment) क्या होता है?",
        "स्वास्थ्य बीमा क्लेम दाखिल करने के लिए कौन से दस्तावेज चाहिए?"
      ],
      ta: [
        "மருத்துவக் காப்பீடு எவற்றை உள்ளடக்கியது?",
        "ஆரம்ப காத்திருப்பு காலத்திற்கும் PED காத்திருப்பு காலத்திற்கும் என்ன வித்தியாசம்?",
        "மருத்துவக் காப்பீட்டில் அறை வாடகை வரம்புகள் (Room-rent limits) என்ன?",
        "மருத்துவக் காப்பீட்டுக் கொள்கையில் இணை கட்டணம் (Co-payment) என்றால் என்ன?",
        "மருத்துவக் காப்பீட்டு கோரிக்கையைத் தாக்கல் செய்ய என்ன ஆவணங்கள் தேவை?"
      ]
    }
  },
  life: {
    id: "life",
    title: "Life Insurance",
    icon: "🛡️",
    questions: {
      en: [
        "How does pure term life insurance work?",
        "Who can be nominated in a life insurance policy?",
        "What happens when a life insurance policy expires?",
        "What is the difference between term insurance and whole life insurance?",
        "What documents are needed to make a life insurance claim?"
      ],
      hi: [
        "प्योर टर्म लाइफ इंश्योरेंस कैसे काम करता है?",
        "जीवन बीमा पॉलिसी में किसे नामांकित (Nominated) किया जा सकता है?",
        "जीवन बीमा पॉलिसी समाप्त होने पर क्या होता है?",
        "टर्म इंश्योरेंस और होल लाइफ इंश्योरेंस में क्या अंतर है?",
        "जीवन बीमा क्लेम करने के लिए कौन से दस्तावेज आवश्यक हैं?"
      ],
      ta: [
        "பியூர் டேர்ம் லைஃப் இன்சூரன்ஸ் எவ்வாறு செயல்படுகிறது?",
        "ஆயுள் காப்பீட்டுக் கொள்கையில் யாரை நாமினியாக நியமிக்கலாம்?",
        "ஆயுள் காப்பீட்டுக் கொள்கை காலாவதியாகும் போது என்ன நடக்கும்?",
        "டேர்ம் இன்சூரன்ஸுக்கும் முழு ஆயுள் காப்பீட்டுக்கும் என்ன வித்தியாசம்?",
        "ஆயுள் காப்பீட்டுக் கோரிக்கையை வைக்க என்ன ஆவணங்கள் தேவை?"
      ]
    }
  },
  motor: {
    id: "motor",
    title: "Motor Insurance",
    icon: "🚗",
    questions: {
      en: [
        "What is the difference between third-party and comprehensive motor insurance?",
        "What is a motor insurance no-claim bonus?",
        "What should I do after a road accident?",
        "What documents are required for a motor insurance claim?",
        "What does zero-depreciation cover mean?"
      ],
      hi: [
        "थर्ड पार्टी और कॉम्प्रिहेंसिव मोटर बीमा में क्या अंतर है?",
        "मोटर बीमा में नो-क्लेम बोनस (NCB) क्या होता है?",
        "सड़क दुर्घटना के बाद मुझे क्या करना चाहिए?",
        "मोटर बीमा क्लेम के लिए कौन से दस्तावेज आवश्यक हैं?",
        "जीरो-डेप्रिसिएशन कवर का क्या अर्थ है?"
      ],
      ta: [
        "தேர்ட் பார்ட்டி மற்றும் காம்ப்ரிஹென்சிவ் வாகனக் காப்பீட்டின் வேறுபாடு என்ன?",
        "வாகன காப்பீட்டில் நோ-கிளைம் போனஸ் (NCB) என்றால் என்ன?",
        "சாலை விபத்துக்குப் பிறகு நான் என்ன செய்ய வேண்டும்?",
        "மோட்டார் காப்பீட்டு உரிமைகோரலுக்கு என்ன ஆவணங்கள் தேவை?",
        "ஜீரோ டெப்ரிசியேஷன் கவர் என்றால் என்ன?"
      ]
    }
  },
  travel: {
    id: "travel",
    title: "Travel Insurance",
    icon: "✈️",
    questions: {
      en: [
        "What does travel insurance cover?",
        "Does travel insurance cover medical emergencies abroad?",
        "What happens if my flight is cancelled?",
        "How do I make a travel insurance claim?",
        "Are pre-existing medical conditions covered by travel insurance?"
      ],
      hi: [
        "यात्रा बीमा में क्या कवर होता है?",
        "क्या यात्रा बीमा विदेश में मेडिकल इमरजेंसी को कवर करता है?",
        "यदि मेरी उड़ान रद्द हो जाती है तो क्या होता है?",
        "मैं यात्रा बीमा क्लेम कैसे करूं?",
        "क्या यात्रा बीमा में पहले से मौजूद बीमारियां कवर होती हैं?"
      ],
      ta: [
        "பயணக் காப்பீடு எவற்றை உள்ளடக்கியது?",
        "பயணக் காப்பீடு வெளிநாட்டில் ஏற்படும் மருத்துவ அவசரநிலைகளை உள்ளடக்குகிறதா?",
        "எனது விமானம் ரத்து செய்யப்பட்டால் என்ன நடக்கும்?",
        "பயணக் காப்பீட்டுக் கோரிக்கையை எவ்வாறு செய்வது?",
        "ஏற்கனவே உள்ள மருத்துவ நிலைமைகள் பயணக் காப்பீட்டில் உள்ளடக்கப்பட்டுள்ளதா?"
      ]
    }
  },
  banking: {
    id: "banking",
    title: "Banking & Accounts",
    icon: "🏦",
    questions: {
      en: [
        "What is the difference between a savings account and a current account?",
        "What is the difference between NEFT, RTGS, and IMPS?",
        "What should I do if a UPI transaction fails?",
        "What is a recurring deposit?",
        "How can I protect myself from banking fraud?"
      ],
      hi: [
        "बचत खाते और चालू खाते में क्या अंतर है?",
        "NEFT, RTGS और IMPS में क्या अंतर है?",
        "यदि यूपीआई लेन-देन विफल हो जाए तो मुझे क्या करना चाहिए?",
        "आवर्ती जमा (Recurring Deposit - RD) क्या है?",
        "मैं बैंकिंग धोखाधड़ी से खुद को कैसे सुरक्षित रख सकता हूं?"
      ],
      ta: [
        "சேமிப்புக் கணக்கிற்கும் நடப்புக் கணக்கிற்கும் என்ன வித்தியாசம்?",
        "NEFT, RTGS மற்றும் IMPS ஆகியவற்றிற்கு இடையே உள்ள வேறுபாடு என்ன?",
        "UPI பரிவர்த்தனை தோல்வியுற்றால் நான் என்ன செய்ய வேண்டும்?",
        "தொடர் வைப்புத்தொகை (Recurring Deposit) என்றால் என்ன?",
        "வங்கி மோசடிகளில் இருந்து என்னை எவ்வாறு பாதுகாத்துக் கொள்வது?"
      ]
    }
  },
  loans: {
    id: "loans",
    title: "Loans & Credit",
    icon: "💳",
    questions: {
      en: [
        "How is an EMI calculated?",
        "What is the difference between a secured and unsecured loan?",
        "What is a loan's interest rate?",
        "What happens if I miss an EMI?",
        "What is loan prepayment?"
      ],
      hi: [
        "ईएमआई (EMI) की गणना कैसे की जाती है?",
        "सुरक्षित (Secured) और असुरक्षित (Unsecured) ऋण में क्या अंतर है?",
        "ऋण की ब्याज दर क्या होती है?",
        "यदि मैं ईएमआई चूक जाऊं तो क्या होगा?",
        "ऋण पूर्व भुगतान (Loan Prepayment) क्या है?"
      ],
      ta: [
        "இஎம்ஐ (EMI) எவ்வாறு கணக்கிடப்படுகிறது?",
        "பாதுகாப்பான கடன் மற்றும் பாதுகாப்பற்ற கடனுக்கு என்ன வித்தியாசம்?",
        "கடனுக்கான வட்டி விகிதம் என்றால் என்ன?",
        "நான் இஎம்ஐ செலுத்த தவறினால் என்ன நடக்கும்?",
        "கடன் முன்கூட்டியே செலுத்துதல் (Loan Prepayment) என்றால் என்ன?"
      ]
    }
  },
  investments: {
    id: "investments",
    title: "Investments",
    icon: "📈",
    questions: {
      en: [
        "What is a mutual fund?",
        "How does a Systematic Investment Plan (SIP) work?",
        "What is the difference between equity and debt funds?",
        "What is diversification?",
        "What risks should I understand before investing?"
      ],
      hi: [
        "म्यूचुअल फंड क्या है?",
        "सिस्टमैटिक इन्वेस्टमेंट प्लान (SIP) कैसे काम करता है?",
        "इक्विटी और डेट फंड में क्या अंतर है?",
        "विविधीकरण (Diversification) क्या है?",
        "निवेश करने से पहले मुझे किन जोखिमों को समझना चाहिए?"
      ],
      ta: [
        "மியூச்சுவல் ஃபண்ட் என்றால் என்ன?",
        "சிப் (SIP) திட்டம் எவ்வாறு செயல்படுகிறது?",
        "ஈக்விட்டி மற்றும் கடன் நிதிகளுக்கு என்ன வித்தியாசம்?",
        "பல்வகைப்படுத்தல் (Diversification) என்றால் என்ன?",
        "முதலீடு செய்வதற்கு முன் நான் என்ன அபாயங்களைப் புரிந்து கொள்ள வேண்டும்?"
      ]
    }
  },
  claims: {
    id: "claims",
    title: "Claims & Grievances",
    icon: "⚖️",
    questions: {
      en: [
        "How do I file an insurance claim?",
        "What documents are commonly needed for an insurance claim?",
        "What should I do if my insurance claim is rejected?",
        "What is the difference between cashless and reimbursement claims?",
        "How can I track a claim's status?"
      ],
      hi: [
        "मैं बीमा क्लेम कैसे दर्ज करूं?",
        "बीमा क्लेम के लिए आमतौर पर कौन से दस्तावेज आवश्यक होते हैं?",
        "यदि मेरा बीमा क्लेम खारिज हो जाए तो मुझे क्या करना चाहिए?",
        "कैशलेस और रीइंबर्समेंट क्लेम में क्या अंतर है?",
        "मैं क्लेम की स्थिति कैसे ट्रैक कर सकता हूं?"
      ],
      ta: [
        "காப்பீட்டுக் கோரிக்கையை எவ்வாறு பதிவு செய்வது?",
        "காப்பீட்டுக் கோரிக்கைக்கு பொதுவாக என்ன ஆவணங்கள் தேவை?",
        "எனது காப்பீட்டுக் கோரிக்கை நிராகரிக்கப்பட்டால் நான் என்ன செய்ய வேண்டும்?",
        "பணமில்லா (Cashless) மற்றும் திருப்பிச் செலுத்தும் (Reimbursement) கோரிக்கைகளுக்கு என்ன வித்தியாசம்?",
        "கிளைம் நிலையை எவ்வாறு கண்காணிப்பது?"
      ]
    }
  },
  // Additional categories under "More"
  personal_finance: {
    id: "personal_finance",
    title: "Personal Finance",
    icon: "💰",
    questions: {
      en: [
        "What is emergency fund planning?",
        "How do Section 80C and 80D tax deductions work?",
        "What is the difference between Old and New Tax Regimes?",
        "How much should I save for retirement?",
        "What is an insurance-to-income ratio?"
      ],
      hi: [
        "इमरजेंसी फंड की योजना कैसे बनाएं?",
        "धारा 80C और 80D टैक्स कटौती कैसे काम करती है?",
        "पुरानी और नई टैक्स व्यवस्था में क्या अंतर है?",
        "मुझे रिटायरमेंट के लिए कितना फंड बचाना चाहिए?",
        "बीमा और आय का सही अनुपात क्या होना चाहिए?"
      ],
      ta: [
        "அவசரகால நிதித் திட்டமிடல் என்றால் என்ன?",
        "பிரிவு 80C மற்றும் 80D வரி விலக்குகள் எவ்வாறு செயல்படுகின்றன?",
        "பழைய மற்றும் புதிய வரி முறைகளுக்கு என்ன வித்தியாசம்?",
        "ஓய்வூதியத்திற்காக நான் எவ்வளவு சேமிக்க வேண்டும்?",
        "காப்பீடு மற்றும் வருமான விகிதம் என்ன?"
      ]
    }
  },
  digital_payments: {
    id: "digital_payments",
    title: "Digital Payments",
    icon: "📱",
    questions: {
      en: [
        "How does UPI transaction security work?",
        "What is the transaction limit for UPI Lite?",
        "What is Aadhaar-enabled Payment System (AePS)?",
        "How to report unauthorized online transactions?",
        "What is tokenization for debit and credit cards?"
      ],
      hi: [
        "यूपीआई लेनदेन सुरक्षा कैसे काम करती है?",
        "UPI Lite की लेनदेन सीमा क्या है?",
        "आधार-सक्षम भुगतान प्रणाली (AePS) क्या है?",
        "अनधिकृत ऑनलाइन लेनदेन की रिपोर्ट कैसे करें?",
        "डेबिट और क्रेडिट कार्ड के लिए टोकनाइज़ेशन क्या है?"
      ],
      ta: [
        "UPI பரிவர்த்தனை பாதுகாப்பு எவ்வாறு செயல்படுகிறது?",
        "UPI Lite பரிவர்த்தனை வரம்பு என்ன?",
        "ஆதார் அடிப்படையிலான கட்டண முறை (AePS) என்றால் என்ன?",
        "அங்கீகரிக்கப்படாத பரிவர்த்தனைகளைப் புகாரளிப்பது எப்படி?",
        "கார்டுகளுக்கான டோக்கனைசேஷன் என்றால் என்ன?"
      ]
    }
  },
  credit_cards: {
    id: "credit_cards",
    title: "Credit Cards",
    icon: "💳",
    questions: {
      en: [
        "How does a credit card grace period work?",
        "What is the difference between total amount due and minimum due?",
        "How does credit card utilization affect CIBIL score?",
        "What are credit card reward points and redemption rules?",
        "How to avoid interest charges on credit cards?"
      ],
      hi: [
        "क्रेडिट कार्ड का ग्रेस पीरियड कैसे काम करता है?",
        "कुल देय राशि और न्यूनतम देय राशि में क्या अंतर है?",
        "क्रेडिट कार्ड उपयोग से सिबिल स्कोर कैसे प्रभावित होता है?",
        "क्रेडिट कार्ड रिवॉर्ड पॉइंट कैसे रिडीम करें?",
        "क्रेडिट कार्ड पर ब्याज शुल्क से कैसे बचें?"
      ],
      ta: [
        "கிரெடிட் கார்டு கிரேஸ் பீரியட் எவ்வாறு செயல்படுகிறது?",
        "மொத்த நிலுவைத் தொகைக்கும் குறைந்தபட்ச நிலுவைத் தொகைக்கும் என்ன வித்தியாசம்?",
        "கிரெடிட் கார்டு பயன்பாடு சிபில் ஸ்கோரை எவ்வாறு பாதிக்கிறது?",
        "கிரெடிட் கார்டு ரிவார்டு புள்ளிகளைப் பெறுவது எப்படி?",
        "கிரெடிட் கார்டு வட்டி கட்டணங்களைத் தவிர்ப்பது எப்படி?"
      ]
    }
  },
  terminology: {
    id: "terminology",
    title: "Insurance Terminology",
    icon: "📖",
    questions: {
      en: [
        "What is Insured Declared Value (IDV)?",
        "What is Free Look Period in insurance policies?",
        "What is Claim Settlement Ratio (CSR)?",
        "What is Subrogation in insurance?",
        "What is Utmost Good Faith (Uberrimae Fidei)?"
      ],
      hi: [
        "बीमित घोषित मूल्य (IDV) क्या है?",
        "बीमा पॉलिसियों में फ्री लुक पीरियड क्या होता है?",
        "क्लेम सेटलमेंट रेशियो (CSR) क्या है?",
        "बीमा में सबरोगेशन (Subrogation) का नियम क्या है?",
        "परम विश्वास (Utmost Good Faith) का सिद्धांत क्या है?"
      ],
      ta: [
        "இன்ஷூர்டு டிக்ளேர்டு வேல்யூ (IDV) என்றால் என்ன?",
        "காப்பீட்டு பாலிசிகளில் ஃப்ரீ லுக் காலம் என்றால் என்ன?",
        "கிளைம் செட்டில்மென்ட் விகிதம் (CSR) என்றால் என்ன?",
        "காப்பீட்டில் சப்ரோகேஷன் என்றால் என்ன?",
        "அதி தீவிர நல்லெண்ணம் (Utmost Good Faith) என்றால் என்ன?"
      ]
    }
  }
};

const PRIMARY_TOPIC_IDS = ["health", "life", "motor", "travel", "banking", "loans", "investments", "claims"];
const MORE_TOPIC_IDS = ["personal_finance", "digital_payments", "credit_cards", "terminology"];

export default function CategoryChips({
  uiLang = "en",
  selectedTopic,
  onSelectTopic,
  onSelectQuestion,
  onCloseSuggestions
}) {
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  const moreMenuRef = useRef(null);

  // Close "More" dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (moreMenuRef.current && !moreMenuRef.current.contains(event.target)) {
        setShowMoreMenu(false);
      }
    }
    if (showMoreMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showMoreMenu]);

  // Handle clicking a topic button: ONLY toggles the topic and suggested questions
  // NEVER calls send, backend, or LLM!
  const handleTopicClick = (topicId) => {
    setShowMoreMenu(false);
    if (selectedTopic === topicId) {
      onCloseSuggestions();
    } else {
      onSelectTopic(topicId);
    }
  };

  const selectedTopicData = selectedTopic ? TOPICS_DATA[selectedTopic] : null;
  const questionsList = selectedTopicData
    ? (selectedTopicData.questions[uiLang] || selectedTopicData.questions.en)
    : [];

  return (
    <div className="topics-interaction-container">
      {/* 1. Compact Topic Bar */}
      <div className="compact-topics-bar">
        <div className="topics-scroll-row">
          <span className="topics-lead-label">POPULAR TOPICS:</span>

          {/* 8 Primary Topic Pill Buttons */}
          {PRIMARY_TOPIC_IDS.map((id) => {
            const topic = TOPICS_DATA[id];
            const isSelected = selectedTopic === id;
            return (
              <button
                key={id}
                type="button"
                className={`topic-pill-btn ${isSelected ? "selected-topic" : ""}`}
                onClick={() => handleTopicClick(id)}
                title={`Click to view 5 suggested questions for ${topic.title}`}
                aria-pressed={isSelected}
              >
                <span className="topic-icon">{topic.icon}</span>
                <span className="topic-name">{topic.title.split(" ")[0]}</span>
              </button>
            );
          })}

          {/* "More ▾" Pill Dropdown */}
          <div className="topic-dropdown-container" ref={moreMenuRef}>
            <button
              type="button"
              className={`topic-pill-btn more-dropdown-btn ${showMoreMenu ? "open" : ""} ${
                MORE_TOPIC_IDS.includes(selectedTopic) ? "selected-topic" : ""
              }`}
              onClick={() => setShowMoreMenu(!showMoreMenu)}
              aria-expanded={showMoreMenu}
              title="More topics & suggested questions"
            >
              <span>More</span>
              <svg
                className={`dropdown-caret ${showMoreMenu ? "rotated" : ""}`}
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>

            {showMoreMenu && (
              <div className="topics-dropdown-menu">
                {MORE_TOPIC_IDS.map((id) => {
                  const topic = TOPICS_DATA[id];
                  const isSelected = selectedTopic === id;
                  return (
                    <button
                      key={id}
                      type="button"
                      className={`dropdown-item-btn ${isSelected ? "active-item" : ""}`}
                      onClick={() => handleTopicClick(id)}
                    >
                      <span className="item-icon">{topic.icon}</span>
                      <span className="item-text">{topic.title}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 2. Suggested Questions Panel (Shown Directly Beneath Topic Bar when Selected) */}
      {selectedTopic && selectedTopicData && (
        <div className="suggested-questions-panel">
          <div className="suggested-panel-header">
            <div className="suggested-panel-title">
              <span className="suggested-topic-icon">{selectedTopicData.icon}</span>
              <strong>{selectedTopicData.title}</strong>
              <span className="suggested-subtitle">— Suggested Questions (Click to insert into input)</span>
            </div>
            <button
              type="button"
              className="suggested-close-btn"
              onClick={onCloseSuggestions}
              title="Close suggestions"
              aria-label="Close suggestions"
            >
              ✕
            </button>
          </div>

          <div className="suggested-questions-grid">
            {questionsList.slice(0, 5).map((q, idx) => (
              <button
                key={idx}
                type="button"
                className="suggested-question-card"
                onClick={() => onSelectQuestion(q)}
                title="Click to place into input box"
              >
                <span className="card-q-icon">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                </span>
                <span className="card-q-text">{q}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
