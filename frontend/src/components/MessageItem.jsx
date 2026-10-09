import React, { useState } from "react";
import { requestTextToSpeech } from "../services/api";

// Helper to format inline markdown like **bold**, *italic*, `code`
function renderInlineFormatting(text) {
  if (!text) return null;
  const parts = [];
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let lastIndex = 0;
  let match;
  let keyIndex = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    const token = match[0];
    if (token.startsWith("**") && token.endsWith("**")) {
      parts.push(<strong key={`b-${keyIndex++}`}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("*") && token.endsWith("*")) {
      parts.push(<em key={`i-${keyIndex++}`}>{token.slice(1, -1)}</em>);
    } else if (token.startsWith("`") && token.endsWith("`")) {
      parts.push(<code key={`c-${keyIndex++}`} className="inline-code">{token.slice(1, -1)}</code>);
    }
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts;
}

// Block markdown renderer that groups paragraphs, numbered lists, bullet lists, and headers
function renderMarkdownContent(content) {
  if (!content) return null;

  const rawBlocks = content.split(/\n{2,}/);
  const elements = [];

  rawBlocks.forEach((block, blockIdx) => {
    const lines = block.trim().split("\n");
    if (lines.length === 0 || !lines[0].trim()) return;

    // Check if block is an ordered list (e.g. "1. ", "2. ")
    const isOrderedList = lines.every((line) => /^\d+\.\s+/.test(line.trim()));
    if (isOrderedList) {
      elements.push(
        <ol key={`ol-${blockIdx}`} className="content-ordered-list">
          {lines.map((line, lineIdx) => {
            const stripped = line.trim().replace(/^\d+\.\s+/, "");
            return <li key={lineIdx}>{renderInlineFormatting(stripped)}</li>;
          })}
        </ol>
      );
      return;
    }

    // Check if block is an unordered list (e.g. "- ", "* ")
    const isUnorderedList = lines.every((line) => /^[-*]\s+/.test(line.trim()));
    if (isUnorderedList) {
      elements.push(
        <ul key={`ul-${blockIdx}`} className="content-unordered-list">
          {lines.map((line, lineIdx) => {
            const stripped = line.trim().replace(/^[-*]\s+/, "");
            return <li key={lineIdx}>{renderInlineFormatting(stripped)}</li>;
          })}
        </ul>
      );
      return;
    }

    // Headings
    if (lines.length === 1 && lines[0].startsWith("### ")) {
      elements.push(
        <h4 key={`h4-${blockIdx}`} className="content-h4">
          {renderInlineFormatting(lines[0].slice(4))}
        </h4>
      );
      return;
    }
    if (lines.length === 1 && lines[0].startsWith("## ")) {
      elements.push(
        <h3 key={`h3-${blockIdx}`} className="content-h3">
          {renderInlineFormatting(lines[0].slice(3))}
        </h3>
      );
      return;
    }

    // Default paragraph (supports embedded newlines as <br />)
    elements.push(
      <p key={`p-${blockIdx}`} className="content-para">
        {lines.map((line, lIdx) => (
          <React.Fragment key={lIdx}>
            {renderInlineFormatting(line)}
            {lIdx < lines.length - 1 && <br />}
          </React.Fragment>
        ))}
      </p>
    );
  });

  return elements;
}

export default function MessageItem({ message, t }) {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [audioError, setAudioError] = useState("");
  const [currentAudio, setCurrentAudio] = useState(null);

  const isUser = message.role === "user";

  const handleSpeak = async () => {
    if (isPlayingAudio) {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
      }
      setIsPlayingAudio(false);
      return;
    }

    setAudioError("");
    setIsPlayingAudio(true);

    const langCode = message.detected_language || "en";
    const textToSpeak = message.content.replace(/⚠️/g, "").replace(/\*/g, "");

    // 1. Try Browser Native Speech Synthesis first
    if ("speechSynthesis" in window) {
      try {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(textToSpeak);
        const localeMap = {
          ta: "ta-IN",
          hi: "hi-IN",
          te: "te-IN",
          kn: "kn-IN",
          ml: "ml-IN",
          en: "en-IN"
        };
        utterance.lang = localeMap[langCode] || "en-IN";
        utterance.rate = 0.95;

        const voices = window.speechSynthesis.getVoices();
        const matchedVoice = voices.find((v) => v.lang === utterance.lang || v.lang.startsWith(langCode));
        if (matchedVoice) {
          utterance.voice = matchedVoice;
        }

        utterance.onend = () => setIsPlayingAudio(false);
        utterance.onerror = async () => {
          await fallbackBackendTTS(textToSpeak, langCode);
        };

        window.speechSynthesis.speak(utterance);
        return;
      } catch (err) {
        console.warn("SpeechSynthesis error, falling back to backend:", err);
      }
    }

    // 2. Fallback to Backend TTS API
    await fallbackBackendTTS(textToSpeak, langCode);
  };

  const fallbackBackendTTS = async (text, lang) => {
    try {
      const res = await requestTextToSpeech(text, lang);
      if (res.success && res.audio_base64) {
        const audio = new Audio(`data:audio/mp3;base64,${res.audio_base64}`);
        setCurrentAudio(audio);
        audio.onended = () => setIsPlayingAudio(false);
        audio.onerror = () => {
          setIsPlayingAudio(false);
          setAudioError(t?.audioError || "Failed to play audio");
        };
        await audio.play();
      } else {
        setIsPlayingAudio(false);
        setAudioError(t?.audioError || "Failed to play audio");
      }
    } catch (err) {
      console.error("Backend TTS error:", err);
      setIsPlayingAudio(false);
      setAudioError(t?.audioError || "Audio service unavailable");
    }
  };

  const docCount = message.sources?.filter((s) => s.source_type === "uploaded_document").length || 0;
  const kbCount = message.sources?.filter((s) => s.source_type !== "uploaded_document").length || 0;

  return (
    <div className={`message-row ${isUser ? "user-row" : "assistant-row"}`}>
      <div className={`message-bubble ${isUser ? "user-bubble" : "assistant-bubble"}`}>
        {/* Bubble Header */}
        <div className="message-header">
          <div className="sender-tag">
            {isUser ? (
              <>
                <span className="sender-avatar">👤</span>
                <span className="sender-name">You</span>
                {message.input_type === "voice" && (
                  <span className="voice-tag" title="Sent via voice input">
                    🎤 Voice
                  </span>
                )}
              </>
            ) : (
              <>
                <span className="sender-avatar">🛡️</span>
                <span className="sender-name">BharatInsure AI</span>
                {message.language_name && (
                  <span className="lang-tag">
                    {message.language_flag || "🇮🇳"} {message.language_name}
                  </span>
                )}
              </>
            )}
          </div>

          {!isUser && (
            <div className="bubble-actions">
              <button
                type="button"
                className={`speaker-btn ${isPlayingAudio ? "playing" : ""}`}
                onClick={handleSpeak}
                title={isPlayingAudio ? "Stop reading" : "Listen to answer"}
                aria-label={isPlayingAudio ? "Stop reading" : "Listen to answer"}
              >
                {isPlayingAudio ? (
                  <>
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
                      <rect x="6" y="6" width="12" height="12" rx="2" />
                    </svg>
                    <span>Stop</span>
                  </>
                ) : (
                  <>
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                      <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                    </svg>
                    <span>Listen</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Message Content with Proper Markdown Rendering */}
        <div className="message-content">
          {renderMarkdownContent(message.content)}
        </div>

        {/* Audio Error Toast */}
        {audioError && <div className="audio-error-msg">⚠️ {audioError}</div>}

        {/* Multi-Source RAG Sources Drawer */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="rag-sources-section">
            <button
              type="button"
              className="sources-toggle-btn"
              onClick={() => setShowSources(!showSources)}
            >
              <div className="sources-toggle-label">
                <span className="sources-icon">📚</span>
                <span className="sources-title">Sources ({message.sources.length})</span>
                {docCount > 0 && (
                  <span className="doc-source-count-badge">📄 {docCount} Doc</span>
                )}
                {kbCount > 0 && (
                  <span className="kb-source-count-badge">📚 {kbCount} Knowledge Base</span>
                )}
              </div>
              <span className="sources-chevron">{showSources ? "▲" : "▼"}</span>
            </button>

            {showSources && (
              <div className="sources-drawer">
                <div className="sources-grid">
                  {message.sources.map((src, idx) => {
                    const isDoc = src.source_type === "uploaded_document";
                    return (
                      <div
                        key={idx}
                        className={`source-card ${isDoc ? "source-uploaded-doc" : "source-knowledge-base"}`}
                      >
                        <div className="source-card-header">
                          <span className={`source-type-pill ${isDoc ? "pill-doc" : "pill-kb"}`}>
                            {isDoc ? "📄 Uploaded Document" : "📚 Knowledge Base"}
                          </span>
                          {src.relevance_score && (
                            <span className="source-score">
                              {Math.round(src.relevance_score * 100)}% Match
                            </span>
                          )}
                        </div>

                        <div className="source-card-title">
                          {isDoc ? (
                            <>
                              <span className="source-doc-name">{src.document_name || src.title}</span>
                              {src.page && (
                                <span className="source-page-badge">Page {src.page}</span>
                              )}
                            </>
                          ) : (
                            <>
                              <span className="source-kb-cat">{src.category}:</span> {src.title}
                            </>
                          )}
                        </div>

                        {src.snippet && (
                          <div className="source-card-snippet">
                            "{src.snippet}"
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Timestamp */}
        <div className="message-time">
          {message.timestamp || new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </div>
      </div>
    </div>
  );
}
