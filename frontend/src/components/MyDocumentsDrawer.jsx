import React from "react";

export default function MyDocumentsDrawer({
  isOpen,
  onClose,
  activeDocument,
  allDocuments = [],
  onRemoveDocument,
  onTriggerUpload,
  onAskAboutDocument
}) {
  if (!isOpen) return null;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-content" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div className="drawer-title-group">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15.5 2H8.6c-.4 0-.8.2-1.1.5-.3.3-.5.7-.5 1.1v12.8c0 .4.2.8.5 1.1.3.3.7.5 1.1.5h9.8c.4 0 .8-.2 1.1-.5.3-.3.5-.7.5-1.1V6.5L15.5 2z" />
              <path d="M3 7.6v12.8c0 .4.2.8.5 1.1.3.3.7.5 1.1.5h9.8" />
              <polyline points="15 2 15 7 20 7" />
            </svg>
            <h3 className="drawer-title">My Documents</h3>
          </div>
          <button type="button" className="drawer-close-btn" onClick={onClose} aria-label="Close documents drawer">
            ✕
          </button>
        </div>

        <div className="drawer-actions-bar">
          <button
            type="button"
            className="drawer-primary-action-btn"
            onClick={() => {
              onTriggerUpload();
              onClose();
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <span>Upload New Document</span>
          </button>
        </div>

        <div className="drawer-body">
          {/* Active Document Section */}
          <div className="docs-section-heading">Active Policy Document</div>

          {activeDocument ? (
            <div className="active-doc-drawer-card">
              <div className="active-card-top">
                <div className="active-card-file-info">
                  <span className="file-svg-badge">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                  </span>
                  <div>
                    <strong className="active-doc-card-title">{activeDocument.document_name}</strong>
                    <div className="active-doc-card-sub">
                      <span>{activeDocument.total_pages} {activeDocument.total_pages === 1 ? "page" : "pages"}</span>
                      <span>•</span>
                      <span>{activeDocument.total_chunks} indexed clauses</span>
                    </div>
                  </div>
                </div>

                <span className="ready-green-badge">
                  <span className="status-dot"></span> Ready for Q&A
                </span>
              </div>

              <div className="active-card-actions">
                <button
                  type="button"
                  className="ask-doc-btn"
                  onClick={() => {
                    onAskAboutDocument(activeDocument.document_name);
                    onClose();
                  }}
                >
                  💬 Ask Question About This Policy
                </button>
                <button
                  type="button"
                  className="remove-doc-btn-danger"
                  onClick={() => {
                    onRemoveDocument();
                  }}
                >
                  ✕ Remove
                </button>
              </div>
            </div>
          ) : (
            <div className="no-active-doc-banner">
              <p>No document currently attached to this chat session.</p>
              <button
                type="button"
                className="inline-upload-link"
                onClick={() => {
                  onTriggerUpload();
                  onClose();
                }}
              >
                Upload a policy PDF or DOCX to ask grounded questions.
              </button>
            </div>
          )}

          {/* Historical Documents in Storage */}
          {allDocuments.length > 0 && (
            <>
              <div className="docs-section-heading" style={{ marginTop: "20px" }}>
                Recent Documents
              </div>
              <div className="recent-docs-list">
                {allDocuments.map((doc, idx) => (
                  <div key={idx} className="recent-doc-item">
                    <div className="recent-doc-info">
                      <span className="doc-icon">📄</span>
                      <div>
                        <span className="recent-doc-name">{doc.document_name}</span>
                        <span className="recent-doc-meta">
                          {doc.total_pages} pages • {doc.uploadedAt || "Indexed"}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
