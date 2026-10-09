import React, { useState, useEffect, useRef } from "react";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import CategoryChips from "./components/CategoryChips";
import MessageItem from "./components/MessageItem";
import InputArea from "./components/InputArea";
import ChatHistoryDrawer from "./components/ChatHistoryDrawer";
import MyDocumentsDrawer from "./components/MyDocumentsDrawer";
import RAGInspectorModal from "./components/RAGInspectorModal";
import { sendChatMessage } from "./services/api";
import { UI_TRANSLATIONS } from "./translations/translations";

export default function App() {
  // 1. Dark Mode / Theme State
  const [isDarkMode, setIsDarkMode] = useState(() => {
    return localStorage.getItem("bharat_theme") === "dark";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", isDarkMode ? "dark" : "light");
    localStorage.setItem("bharat_theme", isDarkMode ? "dark" : "light");
  }, [isDarkMode]);

  // 2. Language State (Supports 6 Indian languages + English)
  const [uiLang, setUiLang] = useState(() => {
    return localStorage.getItem("bharat_lang") || "en";
  });

  const handleLanguageChange = (langCode) => {
    setUiLang(langCode);
    localStorage.setItem("bharat_lang", langCode);
  };

  const t = UI_TRANSLATIONS[uiLang] || UI_TRANSLATIONS.en;

  // 3. Multi-Session Chat History Persistence
  const [sessions, setSessions] = useState(() => {
    try {
      const saved = localStorage.getItem("bharat_insure_sessions");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Track uploaded documents in storage
  const [allDocuments, setAllDocuments] = useState(() => {
    try {
      const saved = localStorage.getItem("bharat_insure_docs");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem("bharat_insure_sessions", JSON.stringify(sessions));
  }, [sessions]);

  useEffect(() => {
    localStorage.setItem("bharat_insure_docs", JSON.stringify(allDocuments));
  }, [allDocuments]);

  // 4. Current Chat State
  const [sessionId, setSessionId] = useState(() => `session-${Date.now()}`);
  const [activeModel] = useState("local_small"); // Ollama local model
  const [isLoading, setIsLoading] = useState(false);
  const [activeDocument, setActiveDocument] = useState(null);
  const [inputText, setInputText] = useState("");

  const createInitialMessages = () => [
    {
      role: "assistant",
      content: `${t.welcomeSubtitle}\n\n${t.disclaimer}`,
      detected_language: uiLang,
      language_name: uiLang === "en" ? "English" : uiLang === "hi" ? "Hindi" : "Tamil",
      language_flag: "🇮🇳",
      sources: [],
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    }
  ];

  const [messages, setMessages] = useState(createInitialMessages);

  // 5. Sidebar & Drawers Navigation State
  const [activeSidebarItem, setActiveSidebarItem] = useState("new_chat");
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isHistoryDrawerOpen, setIsHistoryDrawerOpen] = useState(false);
  const [isDocsDrawerOpen, setIsDocsDrawerOpen] = useState(false);
  const [isRAGModalOpen, setIsRAGModalOpen] = useState(false);

  // 6. Interactive Popular Topics State (NEVER auto-sends)
  const [selectedTopic, setSelectedTopic] = useState(null);

  // External trigger refs for sidebar buttons (Voice & Document Upload)
  const triggerVoiceRef = useRef(null);
  const triggerUploadRef = useRef(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Sync current conversation to sessions list
  const updateCurrentSessionInStorage = (newMessages, doc = activeDocument) => {
    setSessions((prev) => {
      const firstUserMsg = newMessages.find((m) => m.role === "user");
      const title = firstUserMsg
        ? (firstUserMsg.content.length > 42 ? `${firstUserMsg.content.slice(0, 40)}...` : firstUserMsg.content)
        : "Insurance Conversation";

      const now = new Date();
      const formattedTime = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) + ", " +
        now.toLocaleDateString([], { month: "short", day: "numeric" });

      const existingIndex = prev.findIndex((s) => s.id === sessionId);
      const sessionObj = {
        id: sessionId,
        title,
        updatedAt: now.toISOString(),
        formattedTime,
        messages: newMessages,
        activeDocument: doc
      };

      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = sessionObj;
        return updated;
      } else {
        return [sessionObj, ...prev];
      }
    });
  };

  // 1. Sidebar Item Click Handlers
  const handleSelectSidebarItem = (itemKey) => {
    setActiveSidebarItem(itemKey);
    setIsMobileSidebarOpen(false);

    if (itemKey === "new_chat") {
      handleNewChat();
    } else if (itemKey === "chat_history") {
      setIsHistoryDrawerOpen(true);
    } else if (itemKey === "upload_doc") {
      if (triggerUploadRef.current) {
        triggerUploadRef.current();
      }
    } else if (itemKey === "voice_input") {
      if (triggerVoiceRef.current) {
        triggerVoiceRef.current();
      }
    } else if (itemKey === "my_docs") {
      setIsDocsDrawerOpen(true);
    }
  };

  // Start fresh conversation without deleting saved history or documents
  const handleNewChat = () => {
    const newId = `session-${Date.now()}`;
    setSessionId(newId);
    setMessages(createInitialMessages());
    setSelectedTopic(null);
    setInputText("");
    setActiveSidebarItem("new_chat");
  };

  // Restore previous session from history
  const handleSelectPastSession = (targetSessionId) => {
    const found = sessions.find((s) => s.id === targetSessionId);
    if (found) {
      setSessionId(found.id);
      setMessages(found.messages || createInitialMessages());
      setActiveDocument(found.activeDocument || null);
      setSelectedTopic(null);
      setInputText("");
      setActiveSidebarItem("chat_history");
    }
  };

  // Delete a session from history
  const handleDeleteSession = (targetSessionId) => {
    setSessions((prev) => prev.filter((s) => s.id !== targetSessionId));
    if (sessionId === targetSessionId) {
      handleNewChat();
    }
  };

  // Handle Suggested Question Click: ONLY fills input field, NEVER sends
  const handleSelectSuggestedQuestion = (questionText) => {
    // If input already has text, preserve or replace cleanly
    setInputText(questionText);
    // Optionally close the suggestions panel or keep it visible
    // Notice: Do NOT call handleSendMessage! User must explicitly send.
  };

  // Handle Send Message (both Text and Voice)
  const handleSendMessage = async (text, inputType = "text") => {
    if (!text.trim()) return;

    const userMsg = {
      role: "user",
      content: text,
      input_type: inputType,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    updateCurrentSessionInStorage(newMessages);
    setIsLoading(true);

    try {
      const response = await sendChatMessage({
        message: text,
        sessionId: sessionId,
        language: "auto",
        modelPreference: activeModel,
        inputType: inputType
      });

      const assistantMsg = {
        role: "assistant",
        content: response.response,
        detected_language: response.detected_language,
        language_name: response.language_name,
        language_flag: response.language_flag,
        sources: response.sources || [],
        model_used: response.model_used,
        latency_ms: response.latency_ms,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };

      const finalMessages = [...newMessages, assistantMsg];
      setMessages(finalMessages);
      updateCurrentSessionInStorage(finalMessages);
    } catch (err) {
      console.error("Chat error:", err);
      const errorMsg = {
        role: "assistant",
        content: `⚠️ ${t.errorMessages?.generic || "An error occurred while contacting the assistant."} (${err.message})`,
        detected_language: uiLang,
        sources: [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };
      const finalMessages = [...newMessages, errorMsg];
      setMessages(finalMessages);
      updateCurrentSessionInStorage(finalMessages);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    const reset = createInitialMessages();
    setMessages(reset);
    updateCurrentSessionInStorage(reset);
  };

  const handleDocumentUploaded = (docData) => {
    setActiveDocument(docData);
    setAllDocuments((prev) => {
      const filtered = prev.filter((d) => d.document_name !== docData.document_name);
      return [
        {
          ...docData,
          uploadedAt: new Date().toLocaleDateString([], { month: "short", day: "numeric" })
        },
        ...filtered
      ];
    });

    const docMsg = {
      role: "assistant",
      content: `📄 **${t.documentReady || "Document ready for questions"}!**\n\n**${docData.document_name}** (${docData.total_pages} ${t.pages || "pages"}, ${docData.total_chunks} ${t.chunks || "chunks"})\n\nYou can now ask specific questions about this policy in English, தமிழ், हिन्दी, or any Indian language. The assistant will search this document first.`,
      detected_language: uiLang,
      sources: [],
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };

    const newMsgs = [...messages, docMsg];
    setMessages(newMsgs);
    updateCurrentSessionInStorage(newMsgs, docData);
  };

  const handleDocumentRemoved = () => {
    const docName = activeDocument?.document_name || "Document";
    setActiveDocument(null);
    const removeMsg = {
      role: "assistant",
      content: `ℹ️ **${docName}** removed. Active session has reverted to the **Base Insurance Knowledge Base**.`,
      detected_language: uiLang,
      sources: [],
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };
    const newMsgs = [...messages, removeMsg];
    setMessages(newMsgs);
    updateCurrentSessionInStorage(newMsgs, null);
  };

  return (
    <div className="app-root-layout">
      {/* 1. Permanent Left Sidebar (ChatGPT-like) */}
      <Sidebar
        activeItem={activeSidebarItem}
        onSelectItem={handleSelectSidebarItem}
        isOpen={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
        activeDocument={activeDocument}
      />

      {/* 2. Main Viewport */}
      <div className="main-viewport">
        {/* Top Header */}
        <Navbar
          uiLang={uiLang}
          onLanguageChange={handleLanguageChange}
          theme={isDarkMode ? "dark" : "light"}
          onToggleTheme={() => setIsDarkMode(!isDarkMode)}
          onClearChat={handleClearChat}
          onToggleMobileSidebar={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
          t={t}
        />

        {/* Main Chat Interactive Workspace */}
        <main className="main-chat-area">
          {/* Interactive Popular Topics Bar & Suggested Questions (NEVER auto-sends) */}
          <CategoryChips
            uiLang={uiLang}
            selectedTopic={selectedTopic}
            onSelectTopic={(topicId) => setSelectedTopic(topicId)}
            onSelectQuestion={handleSelectSuggestedQuestion}
            onCloseSuggestions={() => setSelectedTopic(null)}
          />

          {/* Scrollable Chat Window */}
          <div className="chat-window">
            <div className="messages-stream">
              {messages.map((msg, index) => (
                <MessageItem
                  key={index}
                  message={msg}
                  t={t}
                />
              ))}

              {/* Thinking / Loading indicator */}
              {isLoading && (
                <div className="message-row assistant-row">
                  <div className="message-bubble assistant-bubble loading-bubble">
                    <div className="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <span className="loading-text">
                      {activeDocument
                        ? `Searching ${activeDocument.document_name} & policy clauses...`
                        : (t.processing || "Thinking...")}
                    </span>
                  </div>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>
          </div>

          {/* Fixed Chat Composer */}
          <InputArea
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            uiLang={uiLang}
            t={t}
            sessionId={sessionId}
            activeDocument={activeDocument}
            onDocumentUploaded={handleDocumentUploaded}
            onDocumentRemoved={handleDocumentRemoved}
            inputText={inputText}
            setInputText={setInputText}
            onRegisterVoiceTrigger={(fn) => {
              triggerVoiceRef.current = fn;
            }}
            onRegisterUploadTrigger={(fn) => {
              triggerUploadRef.current = fn;
            }}
          />

          {/* Footer Disclaimer */}
          <footer className="legal-disclaimer">
            <p>{t.disclaimer}</p>
            <button
              type="button"
              className="footer-kb-link"
              onClick={() => setIsRAGModalOpen(true)}
            >
              📚 View Indexed IRDAI Knowledge Base & Document Chunks
            </button>
          </footer>
        </main>
      </div>

      {/* 3. Drawers & Modals */}
      <ChatHistoryDrawer
        isOpen={isHistoryDrawerOpen}
        onClose={() => setIsHistoryDrawerOpen(false)}
        sessions={sessions}
        currentSessionId={sessionId}
        onSelectSession={handleSelectPastSession}
        onDeleteSession={handleDeleteSession}
        onNewChat={handleNewChat}
      />

      <MyDocumentsDrawer
        isOpen={isDocsDrawerOpen}
        onClose={() => setIsDocsDrawerOpen(false)}
        activeDocument={activeDocument}
        allDocuments={allDocuments}
        onRemoveDocument={handleDocumentRemoved}
        onTriggerUpload={() => {
          if (triggerUploadRef.current) {
            triggerUploadRef.current();
          }
        }}
        onAskAboutDocument={(docName) => {
          setInputText(`What are the key policy benefits and exclusions in ${docName}?`);
        }}
      />

      <RAGInspectorModal
        isOpen={isRAGModalOpen}
        onClose={() => setIsRAGModalOpen(false)}
        t={t}
        sessionId={sessionId}
      />
    </div>
  );
}
