

import React, { useState } from "react";
import axios from "axios";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./App.css";

function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Collapsed states per-claim index (collapsed by default: undefined => collapsed)
  const [collapsedRag, setCollapsedRag] = useState({});
  const [collapsedTrusted, setCollapsedTrusted] = useState({});
  const [collapsedUntrusted, setCollapsedUntrusted] = useState({});

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!url.trim()) {
      toast.error("Please enter a YouTube URL");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(
        "http://localhost:4000/api/videos/process-video",
        { url: url.trim() },
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer factchecker-api-key-123",
          },
          timeout: 4000000,
        }
      );

      setResult(response.data);
      toast.success("Video processed successfully!");
    } catch (err) {
      console.error("Error:", err);
      const errorMessage =
        err.response?.data?.detail || err.message || "An error occurred";
      setError(errorMessage);
      toast.error(`Error: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    setResult(null);
    setError(null);
    setUrl("");
    setCollapsedRag({});
    setCollapsedTrusted({});
    setCollapsedUntrusted({});
  };

  const formatDate = (dateString) => {
    if (!dateString) return "Unknown";
    return new Date(dateString).toLocaleString();
  };

  // Helpers for source display
  const getSourceIcon = (source) => {
    if (!source) return "📄";
    if (source.source_type === "rag") return "📚";
    if (source.source_type === "web") return source.trusted ? "🔍" : "🌐";
    return "📄";
  };

  const renderTrustBadge = (source) => {
    if (!source) return null;
    if (source.source_type === "rag") {
      return <span className="source-type-badge rag">RAG evidence</span>;
    }
    if (source.trusted) {
      return <span className="source-type-badge trusted">Trusted web</span>;
    }
    return (
      <span className="source-type-badge untrusted">General web (untrusted)</span>
    );
  };

  const groupSources = (sources = []) => {
    const rag = [];
    const webTrusted = [];
    const webUntrusted = [];
    for (const s of sources) {
      if (s.source_type === "rag") rag.push(s);
      else if (s.source_type === "web" && s.trusted) webTrusted.push(s);
      else if (s.source_type === "web" && !s.trusted) webUntrusted.push(s);
    }
    return { rag, webTrusted, webUntrusted };
  };

  // Toggle helpers (default is collapsed; undefined or true = collapsed)
  const toggleRag = (claimIdx) => {
    setCollapsedRag((prev) => {
      const isCollapsed = prev[claimIdx] !== false;
      return { ...prev, [claimIdx]: !isCollapsed };
    });
  };
  const toggleTrusted = (claimIdx) => {
    setCollapsedTrusted((prev) => {
      const isCollapsed = prev[claimIdx] !== false;
      return { ...prev, [claimIdx]: !isCollapsed };
    });
  };
  const toggleUntrusted = (claimIdx) => {
    setCollapsedUntrusted((prev) => {
      const isCollapsed = prev[claimIdx] !== false;
      return { ...prev, [claimIdx]: !isCollapsed };
    });
  };

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <h1>🩺 AI Diabetes MythBuster</h1>
          <p>Fact-check diabetes claims in YouTube videos</p>
        </header>

        <form onSubmit={handleSubmit} className="form">
          <div className="input-group">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter YouTube video URL (e.g., https://youtube.com/watch?v=...)"
              className="url-input"
              disabled={loading}
            />
            <button
              type="submit"
              className="submit-btn"
              disabled={loading || !url.trim()}
            >
              {loading ? "🔄 Processing..." : "🔍 Analyze Video"}
            </button>
          </div>
        </form>

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Downloading and analyzing video... This may take a moment.</p>
          </div>
        )}

        {error && (
          <div className="error-card">
            <h3>❌ Error</h3>
            <p>{error}</p>
            <button onClick={clearResults} className="clear-btn">
              Try Again
            </button>
          </div>
        )}

        {result && (
          <div className="results">
            <div className="success-header">
              <h2>✅ Analysis Complete</h2>
              <button onClick={clearResults} className="clear-btn">
                Analyze New Video
              </button>
            </div>

            {/* Video Information */}
            <div className="card">
              <h3>📁 Video Information</h3>
              <p>
                <strong>Title:</strong> {result.title || "Unknown"}
              </p>
              <p>
                <strong>Video ID:</strong> {result.videoID || "Unknown"}
              </p>
              <p>
                <strong>Source:</strong>{" "}
                {result.from_cache ? "⚡ Cached (instant result)" : "🔄 Freshly processed"}
              </p>
              <p>
                <strong>Processed At:</strong> {formatDate(result.processed_at)}
              </p>
              <p>
                <strong>URL:</strong>{" "}
                <a
                  href={result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="url-link"
                >
                  {result.url?.length > 50
                    ? result.url.substring(0, 50) + "..."
                    : result.url}
                </a>
              </p>
            </div>

            {/* Transcription */}
            <div className="card">
              <h3>🎤 Video Transcription</h3>
              <div className="transcription-box">
                {result.transcription ? (
                  <p className="transcription-text">{result.transcription}</p>
                ) : (
                  <p className="error-text">No transcription available</p>
                )}
              </div>
            </div>

            {/* Claims Analysis */}
            <div className="card">
              <h3>🔍 Diabetes Claims Analysis & Fact-Checking</h3>
              {result.claims && result.claims.length > 0 ? (
                <div className="claims-section">
                  <p className="claims-intro">
                    Found {result.claims.length} diabetes-related claim(s) with medical fact-checks:
                  </p>

                  <div className="claims-list">
                    {result.verdicts && result.verdicts.length > 0
                      ? result.verdicts.map((verdict, index) => {
                          const { rag, webTrusted, webUntrusted } = groupSources(
                            verdict.sources
                          );
                          // Collapsed by default unless explicitly set to false
                          const ragCollapsed = collapsedRag[index] !== false;
                          const trustedCollapsed = collapsedTrusted[index] !== false;
                          const untrustedCollapsed = collapsedUntrusted[index] !== false;

                          return (
                            <div
                              key={index}
                              className={`claim-item verdict-${verdict.verdict?.toLowerCase()}`}
                            >
                              <div className="claim-header">
                                <div className="claim-number">{index + 1}</div>
                                <div
                                  className={`verdict-badge verdict-${verdict.verdict?.toLowerCase()}`}
                                >
                                  {verdict.verdict === "TRUE" && "✅ TRUE"}
                                  {verdict.verdict === "FALSE" && "❌ FALSE"}
                                  {verdict.verdict === "PARTIALLY_TRUE" && "⚠️ PARTIAL"}
                                  {verdict.verdict === "INSUFFICIENT_INFO" && "❓ UNCLEAR"}
                                </div>
                              </div>

                              <div className="claim-text" dir="rtl">
                                {verdict.claim}
                              </div>
                              <div className="medical-reasoning" dir="rtl">
                                <strong>Medical Explanation:</strong> {verdict.reasoning}
                              </div>
                              <div className="medical-category">
                                <strong>Category:</strong> {verdict.medical_category}
                              </div>

                              {/* Sources */}
                              {(rag.length > 0 || webTrusted.length > 0 || webUntrusted.length > 0) ? (
                                <div className="sources-section">
                                  <h4 className="sources-heading">📚 Evidence & Sources</h4>

                                  {/* RAG group (collapsible) */}
                                  {rag.length > 0 && (
                                    <div className="sources-group rag-group">
                                      <button
                                        type="button"
                                        className="sources-group-header collapsible"
                                        aria-expanded={!ragCollapsed}
                                        aria-controls={`rag-panel-${index}`}
                                        onClick={() => toggleRag(index)}
                                      >
                                        <span>
                                          📚 <strong>RAG evidence</strong> ({rag.length})
                                        </span>
                                        <span
                                          className="chevron"
                                          style={{
                                            marginLeft: 8,
                                            display: "inline-block",
                                            transition: "transform 0.18s ease",
                                            transform: ragCollapsed ? "rotate(0deg)" : "rotate(180deg)",
                                          }}
                                        >
                                          ▾
                                        </span>
                                      </button>

                                      <div
                                        id={`rag-panel-${index}`}
                                        style={{ display: ragCollapsed ? "none" : "block" }}
                                      >
                                        <div className="sources-list">
                                          {rag.map((source, sourceIndex) => (
                                            <div key={`rag-${index}-${sourceIndex}`} className="source-item trusted-source">
                                              <div className="source-header">
                                                <div className="source-name-container">
                                                  <span className="source-icon">{getSourceIcon(source)}</span>
                                                  <span className="source-name">
                                                    {source.source_url ? (
                                                      <a
                                                        href={source.source_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="source-link"
                                                      >
                                                        {source.source_name || "Source"}
                                                      </a>
                                                    ) : (
                                                      source.source_name || "Source"
                                                    )}
                                                  </span>
                                                  {renderTrustBadge(source)}
                                                </div>
                                                <span
                                                  className={`relevance-badge ${
                                                    source.relevance_badge || "primary"
                                                  }`}
                                                >
                                                  {source.relevance_display || "Most Relevant"}
                                                </span>
                                              </div>

                                              <div className="source-preview">
                                                {source.content_preview}
                                              </div>
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    </div>
                                  )}

                                  {/* Trusted web group (collapsible) */}
                                  {webTrusted.length > 0 && (
                                    <div className="sources-group web-trusted-group">
                                      <button
                                        type="button"
                                        className="sources-group-header collapsible"
                                        aria-expanded={!trustedCollapsed}
                                        aria-controls={`trusted-panel-${index}`}
                                        onClick={() => toggleTrusted(index)}
                                      >
                                        <span>
                                          🔍 <strong>Trusted web</strong> ({webTrusted.length})
                                        </span>
                                        <span
                                          className="chevron"
                                          style={{
                                            marginLeft: 8,
                                            display: "inline-block",
                                            transition: "transform 0.18s ease",
                                            transform: trustedCollapsed ? "rotate(0deg)" : "rotate(180deg)",
                                          }}
                                        >
                                          ▾
                                        </span>
                                      </button>

                                      <div
                                        id={`trusted-panel-${index}`}
                                        style={{ display: trustedCollapsed ? "none" : "block" }}
                                      >
                                        <div className="sources-list">
                                          {webTrusted.map((source, sourceIndex) => (
                                            <div key={`tweb-${index}-${sourceIndex}`} className="source-item trusted-source">
                                              <div className="source-header">
                                                <div className="source-name-container">
                                                  <span className="source-icon">{getSourceIcon(source)}</span>
                                                  <span className="source-name">
                                                    {source.source_url ? (
                                                      <a
                                                        href={source.source_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="source-link"
                                                      >
                                                        {source.source_name || "Source"}
                                                      </a>
                                                    ) : (
                                                      source.source_name || "Source"
                                                    )}
                                                  </span>
                                                  {renderTrustBadge(source)}
                                                </div>
                                                <span
                                                  className={`relevance-badge ${
                                                    source.relevance_badge || "secondary"
                                                  }`}
                                                >
                                                  {source.relevance_display || "Moderately Relevant"}
                                                </span>
                                              </div>

                                              <div className="source-preview">
                                                {source.content_preview}
                                              </div>
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    </div>
                                  )}

                                  {/* Untrusted web group (collapsible, default collapsed) */}
                                  {webUntrusted.length > 0 && (
                                    <div className="sources-group web-untrusted-group">
                                      <button
                                        type="button"
                                        className="sources-group-header collapsible"
                                        aria-expanded={!untrustedCollapsed}
                                        aria-controls={`untrusted-panel-${index}`}
                                        onClick={() => toggleUntrusted(index)}
                                      >
                                        <span>
                                          🌐 <strong>General web (untrusted)</strong> ({webUntrusted.length})
                                        </span>
                                        <span
                                          className="chevron"
                                          style={{
                                            marginLeft: 8,
                                            display: "inline-block",
                                            transition: "transform 0.18s ease",
                                            transform: untrustedCollapsed ? "rotate(0deg)" : "rotate(180deg)",
                                          }}
                                        >
                                          ▾
                                        </span>
                                      </button>

                                      <div
                                        id={`untrusted-panel-${index}`}
                                        style={{ display: untrustedCollapsed ? "none" : "block" }}
                                      >
                                        <p className="untrusted-note">
                                          Items below are not on our trusted medical list; we include them for transparency.
                                        </p>
                                        <div className="sources-list">
                                          {webUntrusted.map((source, sourceIndex) => (
                                            <div key={`uweb-${index}-${sourceIndex}`} className="source-item untrusted-source">
                                              <div className="source-header">
                                                <div className="source-name-container">
                                                  <span className="source-icon">{getSourceIcon(source)}</span>
                                                  <span className="source-name">
                                                    {source.source_url ? (
                                                      <a
                                                        href={source.source_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="source-link"
                                                      >
                                                        {source.source_name || "Source"}
                                                      </a>
                                                    ) : (
                                                      source.source_name || "Source"
                                                    )}
                                                  </span>
                                                  {renderTrustBadge(source)}
                                                </div>
                                                <span
                                                  className={`relevance-badge ${
                                                    source.relevance_badge || "neutral"
                                                  }`}
                                                >
                                                  {source.relevance_display || "Supporting Evidence"}
                                                </span>
                                              </div>

                                              <div className="source-preview">
                                                {source.content_preview}
                                              </div>
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <div className="no-sources">No supporting sources were attached for this claim.</div>
                              )}
                            </div>
                          );
                        })
                      : // Fallback if no verdicts yet
                        result.claims.map((claim, index) => (
                          <div key={index} className="claim-item">
                            <div className="claim-number">{index + 1}</div>
                            <div className="claim-text" dir="rtl">{claim}</div>
                            <div className="claim-actions">
                              <span className="processing-note">Fact-check processing...</span>
                            </div>
                          </div>
                        ))}
                  </div>
                </div>
              ) : (
                <div className="no-claims">
                  <p>ℹ️ This video does not contain diabetes-related claims.</p>
                  <small>
                    The AI analyzed the content and determined it's not about diabetes.
                  </small>
                </div>
              )}
            </div>

            {/* Processing Status */}
            <div className="card">
              <h3>📊 Processing Status</h3>
              <div className="status-info">
                <p>
                  <strong>Status:</strong>{" "}
                  <span className={`status ${result.success ? "success" : "error"}`}>
                    {result.success ? "✅ Success" : "❌ Failed"}
                  </span>
                </p>
                <p>
                  <strong>Message:</strong> {result.message}
                </p>
                {result.from_cache && (
                  <p className="cache-info">
                    ⚡ This result was retrieved from cache, saving time and resources!
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
      />
    </div>
  );
}

export default App;
