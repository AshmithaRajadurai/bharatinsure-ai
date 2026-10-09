import React, { useState, useEffect } from "react";
import { retrieveDocuments, getCurrentDocument } from "../services/api";

export default function RAGInspectorModal({ isOpen, onClose, t, sessionId = "default-session" }) {
  const [query, setQuery] = useState("What is the waiting period for pre-existing diseases?");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [detectedLang, setDetectedLang] = useState("");
  const [activeDoc, setActiveDoc] = useState(null);

  useEffect(() => {
    if (isOpen) {
      getCurrentDocument(sessionId).then((doc) => {
        if (doc && doc.active) {
          setActiveDoc(doc);
        } else {
          setActiveDoc(null);
        }
      }).catch(() => {});
      // Run initial search
      handleSearch();
    }
  }, [isOpen, sessionId]);

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await retrieveDocuments(query, sessionId);
      setResults(data.results || []);
      setDetectedLang(data.detected_language || "en");
      if (data.active_document) {
        setActiveDoc(prev => prev || { document_name: data.active_document });
      }
    } catch (err) {
      console.error("RAG search failed:", err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal-card rag-modal">
        <div className="modal-header">
          <div className="modal-title-group">
            <span className="modal-icon">🔍</span>
            <div>
              <h2 className="modal-title">RAG Knowledge Base & Document Inspector</h2>
              <p className="modal-subtitle">
                Inspect how queries retrieve and rank evidence across Base Knowledge Base and Session Uploaded Documents.
              </p>
            </div>
          </div>
          <button type="button" className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          {/* Active Document Status in Inspector */}
          {activeDoc && activeDoc.document_name && (
            <div className="inspector-doc-banner">
              <span className="doc-icon">📄</span>
              <span>
                Active Session Document: <strong>{activeDoc.document_name}</strong>
                {activeDoc.total_pages ? ` (${activeDoc.total_pages} pages • ${activeDoc.total_chunks} chunks)` : ""}
              </span>
            </div>
          )}

          <form className="rag-search-form" onSubmit={handleSearch}>
            <input
              type="text"
              className="rag-search-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter search query (e.g., room rent limit, waiting period)..."
            />
            <button type="submit" className="rag-search-btn" disabled={loading}>
              {loading ? "Searching..." : "Inspect Retrieval"}
            </button>
          </form>

          {detectedLang && (
            <div className="rag-detected-info">
              <span>Query: <em>"{query}"</em></span> • 
              <span> Language: <strong>{detectedLang.toUpperCase()}</strong></span> • 
              <span> Retrieved Chunks: <strong>{results.length}</strong> (Filtered by threshold ≥ 0.25)</span>
            </div>
          )}

          <div className="rag-threshold-badge" style={{ margin: "8px 0 16px 0", fontSize: "0.82rem", color: "#64748b", background: "rgba(100, 116, 139, 0.08)", padding: "6px 12px", borderRadius: "8px" }}>
            ⚖️ <strong>Hybrid Scoring Formula:</strong> 0.50 × TF-IDF + 0.30 × Semantic/N-gram + 0.20 × Keyword/Title | Chunks with score &lt; 0.25 are discarded.
          </div>

          <div className="rag-results-list">
            {results.length === 0 ? (
              <div className="rag-empty-state" style={{ padding: "24px", textAlign: "center", background: "rgba(239, 68, 68, 0.05)", borderRadius: "12px", border: "1px dashed rgba(239, 68, 68, 0.3)" }}>
                <span style={{ fontSize: "2rem" }}>🛡️</span>
                <h4 style={{ margin: "8px 0 4px 0", color: "#ef4444" }}>No Chunks Passed Relevance Threshold</h4>
                <p style={{ margin: 0, fontSize: "0.88rem", color: "#64748b" }}>
                  The query did not yield high-confidence insurance matches (all scores &lt; 0.25). 
                  BharatInsure AI prevents irrelevant context from poisoning the LLM prompt.
                </p>
              </div>
            ) : (
              results.map((item, idx) => {
                const isDoc = item.source_type === "uploaded_document";
                return (
                  <div
                    key={idx}
                    className={`rag-result-card ${isDoc ? "rag-card-doc" : "rag-card-kb"}`}
                  >
                    <div className="rag-result-meta">
                      <span className={`rag-source-type ${isDoc ? "type-doc" : "type-kb"}`}>
                        {isDoc ? "📄 Uploaded Document" : "📚 Existing Knowledge Base"}
                      </span>
                      <span className="rag-score-tag">
                        Final Score: <strong>{item.relevance_score.toFixed(3)}</strong>
                      </span>
                      {item.page && (
                        <span className="rag-page-tag">Page {item.page}</span>
                      )}
                      <span className="rag-id-tag">ID: {item.id}</span>
                    </div>

                    <div className="rag-scores-breakdown" style={{ display: "flex", gap: "8px", margin: "6px 0", fontSize: "0.78rem" }}>
                      <span style={{ background: "rgba(59, 130, 246, 0.12)", color: "#2563eb", padding: "2px 8px", borderRadius: "4px" }}>
                        TF-IDF: <strong>{item.tfidf_score !== undefined && item.tfidf_score !== null ? item.tfidf_score.toFixed(3) : "—"}</strong>
                      </span>
                      <span style={{ background: "rgba(16, 185, 129, 0.12)", color: "#059669", padding: "2px 8px", borderRadius: "4px" }}>
                        Semantic: <strong>{item.semantic_score !== undefined && item.semantic_score !== null ? item.semantic_score.toFixed(3) : "—"}</strong>
                      </span>
                      <span style={{ background: "rgba(245, 158, 11, 0.12)", color: "#d97706", padding: "2px 8px", borderRadius: "4px" }}>
                        Keyword: <strong>{item.keyword_score !== undefined && item.keyword_score !== null ? item.keyword_score.toFixed(3) : "—"}</strong>
                      </span>
                    </div>

                    <h4 className="rag-result-title">
                      {isDoc ? (item.document_name || item.title) : `${item.category}: ${item.title}`}
                    </h4>

                    <p className="rag-result-snippet">{item.snippet}</p>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
