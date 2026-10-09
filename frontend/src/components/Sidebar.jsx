import React from "react";

export default function Sidebar({
  activeItem,
  onSelectItem,
  isOpen,
  onCloseMobile,
  activeDocument
}) {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="sidebar-mobile-backdrop"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      <aside className={`app-sidebar ${isOpen ? "sidebar-open" : ""}`}>
        {/* Top Header / Actions in Exact Required Order:
            1. New Chat — icon: message-square-plus
            2. Chat History — icon: history
            3. Upload Document — icon: upload
            4. Voice Input — icon: microphone
            5. My Documents — icon: files
        */}
        <div className="sidebar-nav-section">
          {/* 1. New Chat */}
          <button
            type="button"
            className={`sidebar-nav-btn ${activeItem === "new_chat" ? "active" : ""}`}
            onClick={() => onSelectItem("new_chat")}
            title="Start a new conversation"
          >
            <span className="sidebar-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                <line x1="12" y1="8" x2="12" y2="14" />
                <line x1="9" y1="11" x2="15" y2="11" />
              </svg>
            </span>
            <span className="sidebar-label">New Chat</span>
          </button>

          {/* 2. Chat History */}
          <button
            type="button"
            className={`sidebar-nav-btn ${activeItem === "chat_history" ? "active" : ""}`}
            onClick={() => onSelectItem("chat_history")}
            title="View previous conversations"
          >
            <span className="sidebar-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                <path d="M3 3v5h5" />
                <path d="M12 7v5l4 2" />
              </svg>
            </span>
            <span className="sidebar-label">Chat History</span>
          </button>

          {/* 3. Upload Document */}
          <button
            type="button"
            className={`sidebar-nav-btn ${activeItem === "upload_doc" ? "active" : ""}`}
            onClick={() => onSelectItem("upload_doc")}
            title="Upload and index policy document"
          >
            <span className="sidebar-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </span>
            <span className="sidebar-label">Upload Document</span>
          </button>

          {/* 4. Voice Input */}
          <button
            type="button"
            className={`sidebar-nav-btn ${activeItem === "voice_input" ? "active" : ""}`}
            onClick={() => onSelectItem("voice_input")}
            title="Activate speech-to-text voice input"
          >
            <span className="sidebar-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="22" />
              </svg>
            </span>
            <span className="sidebar-label">Voice Input</span>
          </button>

          {/* 5. My Documents */}
          <button
            type="button"
            className={`sidebar-nav-btn ${activeItem === "my_docs" ? "active" : ""}`}
            onClick={() => onSelectItem("my_docs")}
            title="View uploaded policy documents"
          >
            <span className="sidebar-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M15.5 2H8.6c-.4 0-.8.2-1.1.5-.3.3-.5.7-.5 1.1v12.8c0 .4.2.8.5 1.1.3.3.7.5 1.1.5h9.8c.4 0 .8-.2 1.1-.5.3-.3.5-.7.5-1.1V6.5L15.5 2z" />
                <path d="M3 7.6v12.8c0 .4.2.8.5 1.1.3.3.7.5 1.1.5h9.8" />
                <polyline points="15 2 15 7 20 7" />
              </svg>
            </span>
            <span className="sidebar-label">My Documents</span>
            {activeDocument && (
              <span className="sidebar-badge-dot" title="Active document loaded"></span>
            )}
          </button>
        </div>

        {/* Bottom Section: Shield Logo and Tagline */}
        <div className="sidebar-footer">
          <div className="sidebar-footer-brand">
            <div className="sidebar-shield-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <path d="m9 12 2 2 4-4" />
              </svg>
            </div>
            <div className="sidebar-footer-text">
              <span className="sidebar-brand-name">BharatInsure AI</span>
              <p className="sidebar-tagline">“Better Decisions for a Secure Tomorrow”</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
