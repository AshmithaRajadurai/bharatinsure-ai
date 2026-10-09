import React from "react";

export default function ChatHistoryDrawer({
  isOpen,
  onClose,
  sessions = [],
  currentSessionId,
  onSelectSession,
  onDeleteSession,
  onNewChat
}) {
  if (!isOpen) return null;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-content" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div className="drawer-title-group">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
              <path d="M3 3v5h5" />
              <path d="M12 7v5l4 2" />
            </svg>
            <h3 className="drawer-title">Chat History</h3>
          </div>
          <button type="button" className="drawer-close-btn" onClick={onClose} aria-label="Close history">
            ✕
          </button>
        </div>

        <div className="drawer-actions-bar">
          <button
            type="button"
            className="drawer-primary-action-btn"
            onClick={() => {
              onNewChat();
              onClose();
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            <span>Start New Chat</span>
          </button>
        </div>

        <div className="drawer-body">
          {sessions.length === 0 ? (
            <div className="drawer-empty-state">
              <span className="empty-icon">💬</span>
              <p className="empty-title">No saved conversations yet</p>
              <p className="empty-desc">Your chat inquiries and policy questions will appear here automatically.</p>
            </div>
          ) : (
            <div className="history-session-list">
              {sessions.map((sess) => {
                const isActive = sess.id === currentSessionId;
                return (
                  <div
                    key={sess.id}
                    className={`history-session-item ${isActive ? "active-session" : ""}`}
                    onClick={() => {
                      onSelectSession(sess.id);
                      onClose();
                    }}
                  >
                    <div className="session-item-main">
                      <div className="session-item-title-row">
                        <strong className="session-item-title" title={sess.title}>
                          {sess.title || "Untitled Conversation"}
                        </strong>
                        {isActive && <span className="active-pill-badge">Active</span>}
                      </div>

                      <div className="session-item-meta">
                        <span>{sess.formattedTime || "Recent"}</span>
                        <span>•</span>
                        <span>{sess.messages?.length || 0} messages</span>
                        {sess.activeDocument && (
                          <>
                            <span>•</span>
                            <span className="sess-doc-tag">📄 {sess.activeDocument.document_name}</span>
                          </>
                        )}
                      </div>
                    </div>

                    <button
                      type="button"
                      className="session-delete-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(sess.id);
                      }}
                      title="Delete conversation"
                      aria-label="Delete conversation"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
