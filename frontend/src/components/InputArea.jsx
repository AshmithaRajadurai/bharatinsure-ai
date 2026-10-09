import React, { useState, useRef, useEffect, useCallback } from "react";
import { uploadSpeechAudio, uploadInsuranceDocument, removeCurrentDocument } from "../services/api";
import { WavRecorder } from "../services/wavRecorder";

export default function InputArea({
  onSendMessage,
  isLoading,
  uiLang,
  t,
  sessionId = "default-session",
  activeDocument = null,
  onDocumentUploaded = () => {},
  onDocumentRemoved = () => {},
  inputText: externalInputText,
  setInputText: externalSetInputText,
  onRegisterVoiceTrigger,
  onRegisterUploadTrigger
}) {
  const [internalInputText, setInternalInputText] = useState("");
  const isControlled = externalInputText !== undefined && externalSetInputText !== undefined;
  const inputText = isControlled ? externalInputText : internalInputText;
  const setInputText = isControlled ? externalSetInputText : setInternalInputText;

  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [micVolume, setMicVolume] = useState(0);
  const [liveTranscription, setLiveTranscription] = useState("");
  const [speechError, setSpeechError] = useState("");
  const [isProcessingAudio, setIsProcessingAudio] = useState(false);

  // Document upload states
  const [isUploadingDoc, setIsUploadingDoc] = useState(false);
  const [docError, setDocError] = useState("");
  const fileInputRef = useRef(null);

  const wavRecorderRef = useRef(null);
  const speechRecognitionRef = useRef(null);
  const isRecordingRef = useRef(false);
  const transcriptionRef = useRef("");
  const inputTextRef = useRef("");
  const timerIntervalRef = useRef(null);
  const volumeIntervalRef = useRef(null);
  const inputElRef = useRef(null);

  // Sync inputTextRef with state
  useEffect(() => {
    inputTextRef.current = inputText;
  }, [inputText]);

  // Clean up all timers on unmount
  useEffect(() => {
    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      if (volumeIntervalRef.current) clearInterval(volumeIntervalRef.current);
      if (speechRecognitionRef.current) {
        try {
          speechRecognitionRef.current.stop();
        } catch {}
      }
      if (wavRecorderRef.current) {
        wavRecorderRef.current.stop().catch(() => {});
      }
    };
  }, []);

  // Send message immediately
  const triggerSend = useCallback((textToSend, inputType = "text") => {
    setLiveTranscription("");
    transcriptionRef.current = "";
    if (!textToSend || !textToSend.trim()) return;
    onSendMessage(textToSend.trim(), inputType);
    setInputText("");
  }, [onSendMessage, setInputText]);

  // Handle successful speech capture
  const handleSpeechCaptured = useCallback((recognizedText) => {
    const text = recognizedText.trim();
    if (!text) {
      setSpeechError(t?.errorMessages?.emptyAudio || "No speech detected. Please speak clearly.");
      return;
    }
    setInputText(text);
    inputTextRef.current = text;
    transcriptionRef.current = text;
  }, [t, setInputText]);

  // Start Voice Recording
  const startRecording = useCallback(async () => {
    setSpeechError("");
    setLiveTranscription("");
    transcriptionRef.current = "";
    setIsRecording(true);
    isRecordingRef.current = true;
    setRecordingSeconds(0);
    setMicVolume(0);

    // 1. Timer counter for duration
    timerIntervalRef.current = setInterval(() => {
      setRecordingSeconds((prev) => prev + 1);
    }, 1000);

    // 2. Start WAV Audio Recorder
    let recorderReady = false;
    try {
      const recorder = new WavRecorder();
      await recorder.start();
      wavRecorderRef.current = recorder;
      recorderReady = true;

      volumeIntervalRef.current = setInterval(() => {
        if (wavRecorderRef.current && isRecordingRef.current) {
          const vol = wavRecorderRef.current.getVolume();
          setMicVolume(vol);
        }
      }, 60);
    } catch (err) {
      console.warn("WavRecorder initialization notice:", err);
    }

    // 3. Initialize Real-Time Web Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let webSpeechStarted = false;

    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;

        const localeMap = {
          ta: "ta-IN",
          hi: "hi-IN",
          te: "te-IN",
          kn: "kn-IN",
          ml: "ml-IN",
          en: "en-IN"
        };
        recognition.lang = localeMap[uiLang] || "en-IN";

        recognition.onresult = (event) => {
          let accumulatedFinal = "";
          let accumulatedInterim = "";

          for (let i = 0; i < event.results.length; i++) {
            const item = event.results[i];
            const transcript = item[0]?.transcript || "";
            if (item.isFinal) {
              accumulatedFinal += transcript + " ";
            } else {
              accumulatedInterim += transcript;
            }
          }

          const combined = (accumulatedFinal + accumulatedInterim).trim();
          if (combined) {
            transcriptionRef.current = combined;
            setLiveTranscription(combined);
            setInputText(combined);
          }
        };

        recognition.onerror = (e) => {
          console.warn("SpeechRecognition event:", e.error);
          if (e.error === "not-allowed" || e.error === "permission-denied") {
            setSpeechError(t?.errorMessages?.micPermission || "Microphone access denied. Please allow microphone permissions.");
          }
        };

        recognition.onend = () => {
          if (isRecordingRef.current) {
            try {
              recognition.start();
            } catch {}
          }
        };

        recognition.start();
        speechRecognitionRef.current = recognition;
        webSpeechStarted = true;
      } catch (e) {
        console.warn("SpeechRecognition startup note:", e);
      }
    }

    if (!webSpeechStarted && !recorderReady) {
      setIsRecording(false);
      isRecordingRef.current = false;
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      setSpeechError(t?.errorMessages?.micPermission || "Microphone not available or access denied.");
    }
  }, [uiLang, t, setInputText]);

  // Stop Voice Recording and Process Result
  const stopRecording = useCallback(async () => {
    isRecordingRef.current = false;
    setIsRecording(false);
    setMicVolume(0);

    if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    if (volumeIntervalRef.current) clearInterval(volumeIntervalRef.current);

    if (speechRecognitionRef.current) {
      try {
        speechRecognitionRef.current.stop();
      } catch {}
    }

    const capturedText = transcriptionRef.current.trim() || inputTextRef.current.trim();

    if (capturedText) {
      if (wavRecorderRef.current) {
        try {
          await wavRecorderRef.current.stop();
        } catch {}
      }
      handleSpeechCaptured(capturedText);
      return;
    }

    // Fallback: If no text was captured via Web Speech, process recorded WAV via backend STT
    if (wavRecorderRef.current) {
      setIsProcessingAudio(true);
      try {
        const wavBlob = await wavRecorderRef.current.stop();
        if (wavBlob && wavBlob.size > 2000) {
          const sttRes = await uploadSpeechAudio(wavBlob, uiLang);
          if (sttRes.success && sttRes.text && sttRes.text.trim()) {
            handleSpeechCaptured(sttRes.text.trim());
          } else {
            setSpeechError(sttRes.error || t?.errorMessages?.emptyAudio || "Could not transcribe audio.");
          }
        } else {
          setSpeechError(t?.errorMessages?.emptyAudio || "No audio captured.");
        }
      } catch (uploadErr) {
        console.error("Audio processing failed:", uploadErr);
        setSpeechError(t?.errorMessages?.emptyAudio || "Audio processing failed.");
      } finally {
        setIsProcessingAudio(false);
      }
    } else {
      setSpeechError(t?.errorMessages?.emptyAudio || "No speech detected.");
    }
  }, [uiLang, t, handleSpeechCaptured]);

  // Register external triggers for sidebar buttons
  useEffect(() => {
    if (onRegisterVoiceTrigger) {
      onRegisterVoiceTrigger(() => {
        if (!isRecordingRef.current) {
          startRecording();
        } else {
          stopRecording();
        }
      });
    }
  }, [onRegisterVoiceTrigger, startRecording, stopRecording]);

  useEffect(() => {
    if (onRegisterUploadTrigger) {
      onRegisterUploadTrigger(() => {
        fileInputRef.current?.click();
      });
    }
  }, [onRegisterUploadTrigger]);

  const handleSend = (e) => {
    e?.preventDefault();
    if (isRecording) {
      stopRecording();
      return;
    }
    if (!inputText.trim()) return;
    triggerSend(inputText.trim(), "text");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  };

  // Document Upload Handlers
  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setDocError("");
    setIsUploadingDoc(true);

    try {
      const res = await uploadInsuranceDocument(file, sessionId);
      if (res.success) {
        onDocumentUploaded({
          document_name: res.document_name,
          file_type: res.file_type,
          total_pages: res.total_pages,
          total_chunks: res.total_chunks
        });
      }
    } catch (err) {
      console.error("Document upload error:", err);
      setDocError(err.message || (t?.uploadFailed || "Document upload failed"));
    } finally {
      setIsUploadingDoc(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleRemoveDoc = async () => {
    setDocError("");
    try {
      await removeCurrentDocument(sessionId);
      onDocumentRemoved();
    } catch (err) {
      console.error("Error removing document:", err);
    }
  };

  // Dynamic placeholder calculation
  const getPlaceholder = () => {
    if (isRecording) {
      return "Listening... Speak in any language...";
    }
    if (activeDocument) {
      const docName = activeDocument.document_name;
      const truncatedName = docName.length > 25 ? `${docName.slice(0, 22)}...` : docName;
      return `Ask a question about ${truncatedName}...`;
    }
    return t?.inputPlaceholder || "Ask about insurance, banking, finance, or upload a policy document...";
  };

  return (
    <div className="input-section-container">
      {/* 1. Compact Active Document Status Bar */}
      {activeDocument && (
        <div className="active-doc-bar">
          <div className="active-doc-left">
            <span className="doc-icon-badge">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            </span>
            <span className="active-doc-tag">ACTIVE DOCUMENT</span>
            <span className="active-doc-filename" title={activeDocument.document_name}>
              {activeDocument.document_name}
            </span>
            <span className="active-doc-meta-counts">
              ({activeDocument.total_pages} {activeDocument.total_pages === 1 ? "page" : "pages"}
              {activeDocument.total_chunks ? ` • ${activeDocument.total_chunks} chunks` : ""})
            </span>
            <span className="active-doc-ready-status">
              <span className="status-dot"></span>
              Document ready
            </span>
          </div>

          <button
            type="button"
            className="remove-doc-action-btn"
            onClick={handleRemoveDoc}
            title="Remove active document"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
            <span>Remove</span>
          </button>
        </div>
      )}

      {/* Uploading Status Strip */}
      {isUploadingDoc && (
        <div className="doc-uploading-strip">
          <div className="doc-spinner-ring"></div>
          <span>Processing document... Extracting clauses and indexing for RAG</span>
        </div>
      )}

      {/* Document Error Warning */}
      {docError && (
        <div className="doc-alert-bar error">
          <div className="alert-content">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{docError}</span>
          </div>
          <button type="button" className="alert-dismiss-btn" onClick={() => setDocError("")}>✕</button>
        </div>
      )}

      {/* Microphone / Speech Error Alert */}
      {speechError && (
        <div className="doc-alert-bar warning">
          <div className="alert-content">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{speechError}</span>
          </div>
          <button
            type="button"
            className="alert-action-btn"
            onClick={() => {
              setSpeechError("");
              startRecording();
            }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Live Recording Status Bar (Active Recording) */}
      {isRecording && (
        <div className="live-recording-indicator-bar">
          <div className="recording-pulse-tag">
            <span className="rec-red-dot"></span>
            <span className="rec-text">Listening... ({recordingSeconds}s)</span>
          </div>
          {liveTranscription ? (
            <div className="rec-transcription-preview">"{liveTranscription}"</div>
          ) : (
            <div className="rec-hint">Speak clearly in any supported language...</div>
          )}
          <button
            type="button"
            className="rec-done-btn"
            onClick={stopRecording}
          >
            Done
          </button>
        </div>
      )}

      {/* 2. Single Aligned Input Row: [ Upload ] [ Mic ] [ Input ] [ Send ] */}
      <form className="single-input-row" onSubmit={handleSend}>
        {/* Hidden File Input */}
        <input
          id="policy-file-input"
          type="file"
          ref={fileInputRef}
          style={{ display: "none" }}
          accept=".pdf,.docx,.txt"
          onChange={handleFileSelect}
        />

        {/* Upload Document Button on Left */}
        <button
          type="button"
          className="row-upload-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading || isUploadingDoc || isRecording}
          title="Upload policy or financial document (PDF, DOCX, TXT)"
        >
          <svg
            className="row-btn-icon"
            width="17"
            height="17"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
          </svg>
          <span className="row-upload-text">Upload Document</span>
        </button>

        {/* Microphone Button Immediately Beside Upload Button */}
        <button
          type="button"
          className={`row-mic-btn ${isRecording ? "recording-active" : ""}`}
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isLoading || isProcessingAudio || isUploadingDoc}
          title={isRecording ? "Stop listening (Click to finish)" : "Voice input (Click to speak in your language)"}
          aria-label={isRecording ? "Stop recording" : "Start voice recording"}
        >
          {isRecording ? (
            <svg
              className="mic-icon-svg active-pulse"
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <rect x="6" y="6" width="12" height="12" rx="2" />
            </svg>
          ) : (
            <svg
              className="mic-icon-svg"
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="22" />
            </svg>
          )}
        </button>

        {/* Large Question Input Field */}
        <div className="row-input-wrapper">
          <input
            ref={inputElRef}
            type="text"
            className={`row-text-input ${isRecording ? "is-listening" : ""} ${activeDocument ? "doc-active" : ""}`}
            value={inputText}
            onChange={(e) => {
              setInputText(e.target.value);
              transcriptionRef.current = e.target.value;
            }}
            onKeyDown={handleKeyDown}
            placeholder={getPlaceholder()}
            disabled={isLoading || isProcessingAudio || isUploadingDoc}
            aria-label="Ask your insurance or finance question"
          />
        </div>

        {/* Circular Blue Send Button on Right */}
        <button
          type="submit"
          className="row-send-btn"
          disabled={isLoading || isProcessingAudio || isUploadingDoc || (!inputText.trim() && !isRecording)}
          title="Send Question"
          aria-label="Send Question"
        >
          {isLoading || isProcessingAudio ? (
            <div className="btn-spinner"></div>
          ) : (
            <svg
              className="send-icon-svg"
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          )}
        </button>
      </form>

      {/* 3. Small Subtle Helper Text Below Input Row */}
      <div className="input-helper-note">
        Ask questions about your policy • Voice input available • Answers grounded in your document.
      </div>
    </div>
  );
}
