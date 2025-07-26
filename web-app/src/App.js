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

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate URL
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
          timeout: 4000000, // 66 minutes - plenty of time for processing
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
  };

  const formatDate = (dateString) => {
    if (!dateString) return "Unknown";
    return new Date(dateString).toLocaleString();
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
                {result.from_cache
                  ? "⚡ Cached (instant result)"
                  : "🔄 Freshly processed"}
              </p>
              <p>
                <strong>Processed At:</strong> {formatDate(result.processed_at)}
              </p>
              <p>
                <strong>URL:</strong>
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

            {/* Claims Analysis with Fact-Checking */}
            <div className="card">
              <h3>🔍 Diabetes Claims Analysis & Fact-Checking</h3>
              {result.claims && result.claims.length > 0 ? (
                <div className="claims-section">
                  <p className="claims-intro">
                    Found {result.claims.length} diabetes-related claim(s) with
                    medical fact-checks:
                  </p>
                  <div className="claims-list">
                    {result.verdicts && result.verdicts.length > 0
                      ? // Show claims with verdicts
                        result.verdicts.map((verdict, index) => (
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
                                {verdict.verdict === "PARTIALLY_TRUE" &&
                                  "⚠️ PARTIAL"}
                                {verdict.verdict === "INSUFFICIENT_INFO" &&
                                  "❓ UNCLEAR"}
                              </div>
                              <div className="confidence-score">
                                {Math.round((verdict.confidence || 0) * 100)}%
                                confidence
                              </div>
                            </div>
                            <div className="claim-text" dir="rtl">
                              {verdict.claim}
                            </div>
                            <div className="medical-reasoning" dir="rtl">
                              <strong>Medical Explanation:</strong>{" "}
                              {verdict.reasoning}
                            </div>
                            <div className="medical-category">
                              <strong>Category:</strong>{" "}
                              {verdict.medical_category}
                            </div>
                          </div>
                        ))
                      : // Fallback: show claims without verdicts
                        result.claims.map((claim, index) => (
                          <div key={index} className="claim-item">
                            <div className="claim-number">{index + 1}</div>
                            <div className="claim-text" dir="rtl">
                              {claim}
                            </div>
                            <div className="claim-actions">
                              <span className="processing-note">
                                Fact-check processing...
                              </span>
                            </div>
                          </div>
                        ))}
                  </div>
                </div>
              ) : (
                <div className="no-claims">
                  <p>ℹ️ This video does not contain diabetes-related claims.</p>
                  <small>
                    The AI analyzed the content and determined it's not about
                    diabetes.
                  </small>
                </div>
              )}
            </div>

            {/* Processing Status */}
            <div className="card">
              <h3>📊 Processing Status</h3>
              <div className="status-info">
                <p>
                  <strong>Status:</strong>
                  <span
                    className={`status ${result.success ? "success" : "error"}`}
                  >
                    {result.success ? "✅ Success" : "❌ Failed"}
                  </span>
                </p>
                <p>
                  <strong>Message:</strong> {result.message}
                </p>
                {result.from_cache && (
                  <p className="cache-info">
                    ⚡ This result was retrieved from cache, saving time and
                    resources!
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
