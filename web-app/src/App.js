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

  // حالات الطيّ لكل ادعاء (افتراضياً مطوي)
  const [collapsedRag, setCollapsedRag] = useState({});
  const [collapsedTrusted, setCollapsedTrusted] = useState({});
  const [collapsedUntrusted, setCollapsedUntrusted] = useState({});

  // ترجمات التصنيفات الطبية
  const CATEGORY_LABELS_AR = {
    treatment: "العلاج",
    prevention: "الوقاية",
    symptoms: "الأعراض",
    causes: "الأسباب",
    diet: "النظام الغذائي",
    lifestyle: "نمط الحياة",
  };
  const tCategory = (val) =>
    CATEGORY_LABELS_AR[(val || "").toLowerCase()] || val || "غير مُصنّف";

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!url.trim()) {
      toast.error("فضلاً أدخل رابط يوتيوب");
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
      toast.success("تم تحليل الفيديو بنجاح!");
    } catch (err) {
      console.error("Error:", err);
      const errorMessage =
        err.response?.data?.detail || err.message || "حدث خطأ غير متوقع";
      setError(errorMessage);
      toast.error(`خطأ: ${errorMessage}`);
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
    if (!dateString) return "غير معروف";
    try {
      return new Date(dateString).toLocaleString("ar-SA");
    } catch {
      return new Date(dateString).toLocaleString();
    }
  };

  // أيقونات المصادر
  const getSourceIcon = (source) => {
    if (!source) return "📄";
    if (source.source_type === "rag") return "📚";
    if (source.source_type === "web") return source.trusted ? "🔍" : "🌐";
    return "📄";
  };

  // شارات نوع المصدر
  const renderTrustBadge = (source) => {
    if (!source) return null;
    if (source.source_type === "rag") {
      return <span className="source-type-badge rag">أدلة RAG</span>;
    }
    if (source.trusted) {
      return <span className="source-type-badge trusted">ويب موثوق</span>;
    }
    return (
      <span className="source-type-badge untrusted">ويب عام (غير موثوق)</span>
    );
  };

  // تجميع المصادر حسب النوع
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

  // تبديل الطيّ
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

  // ترجمة شارة الصلة إن أتت من الـ API بنص إنجليزي (fallback)
  const tRelevance = (text, idx) => {
    if (text === "Most Relevant" || (!text && idx === 0)) return "الأكثر صلة";
    if (text === "Moderately Relevant" || (!text && idx === 1))
      return "متوسط الصلة";
    if (text === "Supporting Evidence" || !text) return "دليل داعم";
    return text; // في حال كانت راجعة بالعربي أصلاً
  };

  return (
    <div className="App" dir="rtl">
      <div className="container">
        <header className="header">
          <h1>🩺 كاشف خرافات السكري</h1>
          <p>تحقّق من ادعاءات السكري في فيديوهات يوتيوب</p>
        </header>

        <form onSubmit={handleSubmit} className="form">
          <div className="input-group">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="أدخل رابط فيديو يوتيوب (مثال: https://youtube.com/watch?v=...)"
              className="url-input"
              disabled={loading}
              dir="ltr" /* الروابط أفضل تبقى LTR */
            />
            <button
              type="submit"
              className="submit-btn"
              disabled={loading || !url.trim()}
            >
              {loading ? "🔄 جاري المعالجة…" : "🔍 تحليل الفيديو"}
            </button>
          </div>
        </form>

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>جاري تنزيل الفيديو وتحليله…</p>
          </div>
        )}

        {error && (
          <div className="error-card">
            <h3>❌ خطأ</h3>
            <p>{error}</p>
            <button onClick={clearResults} className="clear-btn">
              المحاولة من جديد
            </button>
          </div>
        )}

        {result && (
          <div className="results">
            <div className="success-header">
              <h2>✅ تم التحليل</h2>
              <button onClick={clearResults} className="clear-btn">
                تحليل فيديو جديد
              </button>
            </div>

            {/* معلومات الفيديو */}
            <div className="card">
              <h3>📁 معلومات الفيديو</h3>

              <p>
                <strong>الرابط:</strong>{" "}
                <a
                  href={result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="url-link"
                  dir="ltr"
                >
                  {result.url?.length > 70
                    ? result.url.substring(0, 70) + "..."
                    : result.url}
                </a>
              </p>
            </div>

            {/* نص التفريغ */}
            <div className="card">
              <h3>🎤 نص التفريغ</h3>
              <div className="transcription-box">
                {result.transcription ? (
                  <p className="transcription-text" dir="rtl">
                    {result.transcription}
                  </p>
                ) : (
                  <p className="error-text">لا يوجد نص تفريغ</p>
                )}
              </div>
            </div>

            {/* تحليل الادعاءات */}
            <div className="card">
              <h3>🔍 تحليل الادعاءات والتحقّق</h3>
              {result.claims && result.claims.length > 0 ? (
                <div className="claims-section">
                  <p className="claims-intro">
                    تم العثور على {result.claims.length} ادعاء(ات) متعلقة
                    بالسكري مع نتائج التحقّق الطبية:
                  </p>

                  <div className="claims-list">
                    {result.verdicts && result.verdicts.length > 0
                      ? result.verdicts.map((verdict, index) => {
                          const { rag, webTrusted, webUntrusted } =
                            groupSources(verdict.sources || []);

                          const ragCollapsed = collapsedRag[index] !== false;
                          const trustedCollapsed =
                            collapsedTrusted[index] !== false;
                          const untrustedCollapsed =
                            collapsedUntrusted[index] !== false;

                          return (
                            <div
                              key={index}
                              className={`claim-item verdict-${(
                                verdict.verdict || ""
                              ).toLowerCase()}`}
                            >
                              <div className="claim-header">
                                <div className="claim-number">{index + 1}</div>
                                <div
                                  className={`verdict-badge verdict-${(
                                    verdict.verdict || ""
                                  ).toLowerCase()}`}
                                >
                                  {verdict.verdict === "TRUE" && "✅ صحيح"}
                                  {verdict.verdict === "FALSE" && "❌ غير صحيح"}
                                  {verdict.verdict === "PARTIALLY_TRUE" &&
                                    "⚠️ صحيح جزئياً"}
                                  {verdict.verdict === "INSUFFICIENT_INFO" &&
                                    "❓ لا توجد أدلة كافية للحكم"}
                                </div>
                              </div>

                              <div className="claim-text" dir="rtl">
                                {"الادعاء: " + verdict.claim}
                              </div>
                              <div className="medical-reasoning" dir="rtl">
                                <strong>التفسير الطبي:</strong>{" "}
                                {verdict.reasoning}
                              </div>
                              <div className="medical-category">
                                <strong>التصنيف:</strong>{" "}
                                {tCategory(verdict.medical_category)}
                              </div>

                              {/* الأدلة والمصادر */}
                              {rag.length > 0 ||
                              webTrusted.length > 0 ||
                              webUntrusted.length > 0 ? (
                                <div className="sources-section">
                                  <h4 className="sources-heading">
                                    الأدلة والمصادر
                                  </h4>

                                  {/* RAG */}
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
                                          📚 <strong>أدلة RAG</strong> (
                                          {rag.length})
                                        </span>
                                        <span
                                          className="chevron"
                                          style={{
                                            marginInlineStart: 8,
                                            display: "inline-block",
                                            transition: "transform 0.18s ease",
                                            transform: ragCollapsed
                                              ? "rotate(0deg)"
                                              : "rotate(180deg)",
                                          }}
                                        >
                                          ▾
                                        </span>
                                      </button>

                                      <div
                                        id={`rag-panel-${index}`}
                                        style={{
                                          display: ragCollapsed
                                            ? "none"
                                            : "block",
                                        }}
                                      >
                                        <div className="sources-list">
                                          {rag.map((source, sourceIndex) => (
                                            <div
                                              key={`rag-${index}-${sourceIndex}`}
                                              className="source-item trusted-source"
                                            >
                                              <div className="source-header">
                                                <div className="source-name-container">
                                                  <span className="source-icon">
                                                    {getSourceIcon(source)}
                                                  </span>
                                                  <span className="source-name">
                                                    {source.source_url ? (
                                                      <a
                                                        href={source.source_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="source-link"
                                                        dir="ltr"
                                                      >
                                                        {source.source_name ||
                                                          "مصدر"}
                                                      </a>
                                                    ) : (
                                                      source.source_name ||
                                                      "مصدر"
                                                    )}
                                                  </span>
                                                </div>
                                                <span
                                                  className={`relevance-badge ${
                                                    source.relevance_badge ||
                                                    "primary"
                                                  }`}
                                                >
                                                  {tRelevance(
                                                    source.relevance_display,
                                                    sourceIndex
                                                  )}
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

                                  {/* ويب موثوق */}
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
                                          🔍{" "}
                                          <strong>مصادر البحث من الويب</strong>{" "}
                                          ({webTrusted.length})
                                        </span>
                                        <span
                                          className="chevron"
                                          style={{
                                            marginInlineStart: 8,
                                            display: "inline-block",
                                            transition: "transform 0.18s ease",
                                            transform: trustedCollapsed
                                              ? "rotate(0deg)"
                                              : "rotate(180deg)",
                                          }}
                                        >
                                          ▾
                                        </span>
                                      </button>

                                      <div
                                        id={`trusted-panel-${index}`}
                                        style={{
                                          display: trustedCollapsed
                                            ? "none"
                                            : "block",
                                        }}
                                      >
                                        <div className="sources-list">
                                          {webTrusted.map(
                                            (source, sourceIndex) => (
                                              <div
                                                key={`tweb-${index}-${sourceIndex}`}
                                                className="source-item trusted-source"
                                              >
                                                <div className="source-header">
                                                  <div className="source-name-container">
                                                    <span className="source-icon">
                                                      {getSourceIcon(source)}
                                                    </span>
                                                    <span className="source-name">
                                                      {source.source_url ? (
                                                        <a
                                                          href={
                                                            source.source_url
                                                          }
                                                          target="_blank"
                                                          rel="noopener noreferrer"
                                                          className="source-link"
                                                          dir="ltr"
                                                        >
                                                          {source.source_name ||
                                                            "مصدر"}
                                                        </a>
                                                      ) : (
                                                        source.source_name ||
                                                        "مصدر"
                                                      )}
                                                    </span>
                                                  </div>
                                                  <span
                                                    className={`relevance-badge ${
                                                      source.relevance_badge ||
                                                      "secondary"
                                                    }`}
                                                  >
                                                    {tRelevance(
                                                      source.relevance_display,
                                                      sourceIndex
                                                    )}
                                                  </span>
                                                </div>

                                                <div className="source-preview">
                                                  {source.content_preview}
                                                </div>
                                              </div>
                                            )
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <div className="no-sources">
                                  لا توجد مصادر داعمة لهذا الادعاء.
                                </div>
                              )}
                            </div>
                          );
                        })
                      : // في حال عدم وصول أحكام بعد
                        result.claims.map((claim, index) => (
                          <div key={index} className="claim-item">
                            <div className="claim-number">{index + 1}</div>
                            <div className="claim-text" dir="rtl">
                              {claim}
                            </div>
                            <div className="claim-actions">
                              <span className="processing-note">
                                جاري التحقّق…
                              </span>
                            </div>
                          </div>
                        ))}
                  </div>
                </div>
              ) : (
                <div className="no-claims">
                  <p>ℹ️ لا توجد ادعاءات متعلقة بالسكري في هذا الفيديو.</p>
                  <small>حدّد الذكاء الاصطناعي أن المحتوى ليس عن السكري.</small>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <ToastContainer
        position="top-left"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={true}
        pauseOnFocusLoss
        draggable
        pauseOnHover
      />
    </div>
  );
}

export default App;
