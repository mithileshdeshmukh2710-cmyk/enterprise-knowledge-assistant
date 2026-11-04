import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function parseSummary(summary) {
  if (!summary) return [];

  const sections = [];
  let currentSection = null;

  summary.split("\n").forEach((rawLine) => {
    const line = rawLine.trim();

    if (!line) return;

    const heading = line.match(/^#{1,3}\s+(.+)$/);

    if (heading) {
      currentSection = {
        title: heading[1].replace(/\*\*/g, ""),
        content: [],
      };
      sections.push(currentSection);
      return;
    }

    if (!currentSection) {
      currentSection = { title: "Summary", content: [] };
      sections.push(currentSection);
    }

    const bullet = line.match(/^[-*]\s+(.+)$/);

    currentSection.content.push({
      type: bullet ? "bullet" : "text",
      text: (bullet ? bullet[1] : line).replace(/\*\*/g, ""),
    });
  });

  return sections;
}

function SummaryContent({ summary }) {
  const sections = parseSummary(summary);

  if (!sections.length) {
    return <p className="no-sources">No summary content is available.</p>;
  }

  return (
    <div className="summary-content">
      {sections.map((section, index) => {
        const bulletItems = section.content.filter(
          (item) => item.type === "bullet"
        );
        const textItems = section.content.filter(
          (item) => item.type === "text"
        );

        return (
          <div className="summary-section" key={`${section.title}-${index}`}>
            <h4>{section.title}</h4>

            {textItems.map((item, itemIndex) => (
              <p key={itemIndex}>{item.text}</p>
            ))}

            {bulletItems.length > 0 && (
              <ul>
                {bulletItems.map((item, itemIndex) => (
                  <li key={itemIndex}>{item.text}</li>
                ))}
              </ul>
            )}
          </div>
        );
      })}
    </div>
  );
}


function VisualDiff({ items = [] }) {
  const counts = items.reduce(
    (total, item) => {
      total[item.type] = (total[item.type] || 0) + 1;
      return total;
    },
    {}
  );

  if (!items.length) {
    return (
      <div className="visual-diff-empty">
        No text differences were found, or the documents contain no extractable text.
      </div>
    );
  }

  return (
    <div className="visual-diff">
      <div className="diff-summary">
        <span className="diff-count diff-added">+ {counts.added || 0} added</span>
        <span className="diff-count diff-removed">− {counts.removed || 0} removed</span>
        <span className="diff-count diff-modified">↔ {counts.modified || 0} modified</span>
        <span className="diff-count diff-unchanged">{counts.unchanged || 0} unchanged</span>
      </div>

      <div className="diff-legend">
        <span><i className="legend-dot added-dot" /> Added in Document B</span>
        <span><i className="legend-dot removed-dot" /> Removed from Document A</span>
        <span><i className="legend-dot modified-dot" /> Modified between versions</span>
        <span><i className="legend-dot unchanged-dot" /> Unchanged</span>
      </div>

      <div className="diff-list">
        {items.map((item, index) => (
          <div
            className={`diff-row diff-row-${item.type}`}
            key={`${item.type}-${index}`}
          >
            {item.type === "modified" ? (
              <>
                <div className="diff-row-meta">
                  <span className="diff-type-label diff-label-modified">
                    ↔ Modified content
                  </span>
                  <span className="diff-pages">
                    {item.page_a != null && `A · p.${item.page_a}`}
                    {item.page_a != null && item.page_b != null && "  |  "}
                    {item.page_b != null && `B · p.${item.page_b}`}
                  </span>
                </div>
                <div className="modified-pair">
                  <div className="modified-version modified-old">
                    <span>OLD · DOCUMENT A</span>
                    <p>{item.old_text}</p>
                  </div>
                  <div className="modified-version modified-new">
                    <span>NEW · DOCUMENT B</span>
                    <p>{item.new_text}</p>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="diff-row-meta">
                  <span className={`diff-type-label diff-label-${item.type}`}>
                    {item.type === "added"
                      ? "+ Added"
                      : item.type === "removed"
                        ? "− Removed"
                        : "Unchanged"}
                  </span>
                  <span className="diff-pages">
                    {item.page_a != null && `A · p.${item.page_a}`}
                    {item.page_a != null && item.page_b != null && "  |  "}
                    {item.page_b != null && `B · p.${item.page_b}`}
                  </span>
                </div>
                <p>{item.text}</p>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [asking, setAsking] = useState(false);

  const [error, setError] = useState("");
  const [documents, setDocuments] = useState([]);
  const [history, setHistory] = useState([]);

  // Document summary states
  const [expandedSummary, setExpandedSummary] = useState(null);
  const [summaries, setSummaries] = useState({});
  const [summaryLoading, setSummaryLoading] = useState({});
  const [summaryErrors, setSummaryErrors] = useState({});

  // Document comparison states
  const [documentA, setDocumentA] = useState("");
  const [documentB, setDocumentB] = useState("");

  const [comparisonQuestion, setComparisonQuestion] = useState(
    "Compare the purpose, structure, methodology, and key information in these documents."
  );

  const [comparisonResult, setComparisonResult] = useState(null);
  const [comparing, setComparing] = useState(false);
  const [comparisonError, setComparisonError] = useState("");

  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [deleting, setDeleting] = useState(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  async function handleUpload() {
    if (!file) {
      setError("Please select a PDF first.");
      return;
    }

    setUploading(true);
    setError("");
    setUploadMessage("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Upload failed.");
      }

      setUploadMessage(
        `${data.filename} indexed successfully. ${data.chunks_indexed} chunks created.`
      );

      // Remove any cached summary for an older version of this file.
      setSummaries((previous) => {
        const updated = { ...previous };
        delete updated[data.filename];
        return updated;
      });

      setExpandedSummary(null);
      setFile(null);

      await loadDocuments();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleAsk() {
    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }

    setAsking(true);
    setError("");
    setAnswer(null);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question,
          top_k: 3,
          history: history,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to get an answer.");
      }

      setAnswer(data);

      setHistory((previous) => [
        ...previous,
        { role: "user", content: question },
        { role: "assistant", content: data.answer },
      ].slice(-10));
    } catch (err) {
      setError(err.message);
    } finally {
      setAsking(false);
    }
  }

  function clearChat() {
    setHistory([]);
    setAnswer(null);
    setQuestion("");
    setError("");
  }

  async function loadDocuments() {
    setDocumentsLoading(true);

    try {
      const response = await fetch(`${API_URL}/documents`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not load documents.");
      }

      setDocuments(data.documents || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setDocumentsLoading(false);
    }
  }

  async function toggleSummary(filename) {
    // Close if this document's summary is already open.
    if (expandedSummary === filename) {
      setExpandedSummary(null);
      return;
    }

    setExpandedSummary(filename);
    setError("");

    // Use cached summary if already fetched.
    if (summaries[filename]) {
      return;
    }

    setSummaryLoading((previous) => ({
      ...previous,
      [filename]: true,
    }));

    setSummaryErrors((previous) => ({
      ...previous,
      [filename]: "",
    }));

    try {
      const response = await fetch(
        `${API_URL}/documents/${encodeURIComponent(filename)}/summary`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not load document summary.");
      }

      setSummaries((previous) => ({
        ...previous,
        [filename]: data,
      }));
    } catch (err) {
      setSummaryErrors((previous) => ({
        ...previous,
        [filename]: err.message,
      }));
    } finally {
      setSummaryLoading((previous) => ({
        ...previous,
        [filename]: false,
      }));
    }
  }

  async function handleDelete(filename) {
    const confirmed = window.confirm(
      `Are you sure you want to delete ${filename}?`
    );

    if (!confirmed) return;

    setDeleting(filename);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/documents/${encodeURIComponent(filename)}`,
        { method: "DELETE" }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Delete failed.");
      }

      setUploadMessage(`${filename} deleted successfully.`);

      setSummaries((previous) => {
        const updated = { ...previous };
        delete updated[filename];
        return updated;
      });

      if (expandedSummary === filename) {
        setExpandedSummary(null);
      }

      await loadDocuments();
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(null);
    }
  }

  async function handleCompare() {
    if (!documentA || !documentB) {
      setComparisonError("Please select both documents.");
      return;
    }

    if (documentA === documentB) {
      setComparisonError("Please select two different documents.");
      return;
    }

    setComparing(true);
    setComparisonError("");
    setComparisonResult(null);

    try {
      const response = await fetch(`${API_URL}/compare`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          document_a: documentA,
          document_b: documentB,
          question: comparisonQuestion,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Document comparison failed.");
      }

      setComparisonResult(data);
    } catch (err) {
      setComparisonError(err.message);
    } finally {
      setComparing(false);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="brand-icon">✦</span>
          <span>KnowledgeAI</span>
        </div>
        <span className="header-label">
          Enterprise Knowledge Assistant
        </span>
      </header>

      <main className="container">
        <section className="hero">
          <p className="eyebrow">AI-POWERED DOCUMENT SEARCH</p>
          <h1>Ask your documents.</h1>
          <p className="subtitle">
            Upload your documents and get accurate answers
            grounded in their content.
          </p>
        </section>

        {/* Upload section */}
        <section className="panel">
          <div className="section-heading">
            <span className="step">01</span>
            <div>
              <h2>Upload documents</h2>
              <p>Upload a PDF to add it to your knowledge base.</p>
            </div>
          </div>

          <div className="upload-area">
            <div className="upload-icon">↑</div>

            <label className="file-label">
              <span>
                {file ? file.name : "Choose a PDF document"}
              </span>

              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={(e) => {
                  setFile(e.target.files[0] || null);
                  setUploadMessage("");
                  setError("");
                }}
              />
            </label>

            <p>PDF files only · Maximum 10 MB</p>
          </div>

          <button
            className="primary-button"
            onClick={handleUpload}
            disabled={uploading || !file}
          >
            {uploading ? "Indexing and summarizing..." : "Upload and index"}
          </button>

          {uploadMessage && (
            <div className="success-message">
              ✓ {uploadMessage}
            </div>
          )}
        </section>

        {/* Knowledge base section */}
        <section className="panel">
          <div className="section-heading">
            <span className="step">02</span>
            <div>
              <h2>Knowledge base</h2>
              <p>Your indexed documents and AI-generated summaries.</p>
            </div>
          </div>

          <button
            className="secondary-button"
            onClick={loadDocuments}
            disabled={documentsLoading}
          >
            {documentsLoading ? "Refreshing..." : "Refresh documents"}
          </button>

          {documents.length === 0 ? (
            <p className="no-sources">
              {documentsLoading
                ? "Loading documents..."
                : "No documents indexed yet."}
            </p>
          ) : (
            <ul className="document-list">
              {documents.map((doc) => {
                const isExpanded = expandedSummary === doc.filename;
                const summaryData = summaries[doc.filename];

                return (
                  <li className="document-item" key={doc.filename}>
                    <div className="document-top">
                      <div className="document-info">
                        <strong>{doc.filename}</strong>
                        <p>
                          {doc.pages} pages · {doc.chunks} chunks
                        </p>
                      </div>

                      <button
                        className="delete-button"
                        onClick={() => handleDelete(doc.filename)}
                        disabled={deleting === doc.filename}
                      >
                        {deleting === doc.filename ? "Deleting..." : "Delete"}
                      </button>
                    </div>

                    <div className="document-actions">
                      <button
                        className="summary-toggle"
                        onClick={() => toggleSummary(doc.filename)}
                        aria-expanded={isExpanded}
                      >
                        <span>✦</span>
                        {isExpanded ? "Hide AI Summary" : "View AI Summary"}
                        <span className="summary-chevron">
                          {isExpanded ? "−" : "+"}
                        </span>
                      </button>
                    </div>

                    {isExpanded && (
                      <div className="summary-panel">
                        {summaryLoading[doc.filename] ? (
                          <div className="summary-loading">
                            <span className="loading-spinner" />
                            Loading AI summary...
                          </div>
                        ) : summaryErrors[doc.filename] ? (
                          <div className="summary-error">
                            {summaryErrors[doc.filename]}
                          </div>
                        ) : summaryData?.summary ? (
                          <>
                            <div className="summary-header">
                              <div>
                                <span className="summary-label">
                                  GENERATED BY GEMINI
                                </span>
                                <h3>Document overview</h3>
                              </div>
                              <span className="summary-status">
                                Summary available
                              </span>
                            </div>

                            <SummaryContent summary={summaryData.summary} />

                            {summaryData.updated_at && (
                              <p className="summary-timestamp">
                                Last updated:{" "}
                                {new Date(
                                  summaryData.updated_at
                                ).toLocaleString()}
                              </p>
                            )}
                          </>
                        ) : (
                          <div className="summary-error">
                            A summary is not available for this document.
                            Try uploading the PDF again to generate one.
                          </div>
                        )}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        {/* Document comparison section */}
        <section className="panel comparison-panel">
          <div className="section-heading">
            <span className="step">03</span>
            <div>
              <h2>Compare documents</h2>
              <p>
                Analyze two documents and discover their differences
                using AI.
              </p>
            </div>
          </div>

          <div className="comparison-selectors">
            <div className="comparison-field">
              <label htmlFor="document-a">First document</label>

              <select
                id="document-a"
                value={documentA}
                onChange={(e) => setDocumentA(e.target.value)}
              >
                <option value="">Select Document A</option>

                {documents.map((doc) => (
                  <option key={doc.filename} value={doc.filename}>
                    {doc.filename}
                  </option>
                ))}
              </select>
            </div>

            <div className="comparison-vs">VS</div>

            <div className="comparison-field">
              <label htmlFor="document-b">Second document</label>

              <select
                id="document-b"
                value={documentB}
                onChange={(e) => setDocumentB(e.target.value)}
              >
                <option value="">Select Document B</option>

                {documents.map((doc) => (
                  <option key={doc.filename} value={doc.filename}>
                    {doc.filename}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <label className="comparison-question-label">
            What would you like to compare?
          </label>

          <textarea
            value={comparisonQuestion}
            onChange={(e) => setComparisonQuestion(e.target.value)}
            rows={3}
            placeholder="e.g. Identify changes in objectives and methodology."
          />

          <button
            className="primary-button"
            onClick={handleCompare}
            disabled={
              comparing ||
              !documentA ||
              !documentB ||
              documentA === documentB ||
              !comparisonQuestion.trim()
            }
          >
            {comparing ? "Comparing documents..." : "Compare with AI"}
          </button>

          {comparisonError && (
            <div className="error-message">
              {comparisonError}
            </div>
          )}

          {comparisonResult && (
            <div className="comparison-result">
              <div className="comparison-result-header">
                <span className="summary-label">
                  AI DOCUMENT ANALYSIS
                </span>
                <h3>Comparison Results</h3>

                <p>
                  {comparisonResult.document_a}
                  {" "}vs{" "}
                  {comparisonResult.document_b}
                </p>

                <div className="comparison-stats">
                  <span>
                    {comparisonResult.pages_document_a} pages
                  </span>
                  <span>
                    {comparisonResult.pages_document_b} pages
                  </span>
                </div>
              </div>

              {comparisonResult.visual_diff && (
                <div className="visual-diff-section">
                  <div className="visual-diff-heading">
                    <span className="summary-label">TEXT-LEVEL ANALYSIS</span>
                    <h3>Visual differences</h3>
                    <p>
                      Exact text changes found between the indexed documents.
                      Semantic interpretation appears below.
                    </p>
                  </div>
                  <VisualDiff items={comparisonResult.visual_diff} />
                </div>
              )}

              <div className="comparison-answer">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {comparisonResult.comparison}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </section>

        {/* Question answering section */}
        <section className="panel">
          <div className="section-heading">
            <span className="step">04</span>
            <div>
              <h2>Ask a question</h2>
              <p>Get answers from your uploaded documents.</p>
            </div>
          </div>

          <div style={{ marginBottom: "15px" }}>
            <button
              className="secondary-button"
              onClick={clearChat}
            >
              New conversation
            </button>
          </div>

          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. How many days can employees work from home?"
            rows="4"
          />

          <button
            className="primary-button"
            onClick={handleAsk}
            disabled={asking || !question.trim()}
          >
            {asking ? "Searching documents..." : "Ask KnowledgeAI"}
          </button>

          {answer && (
            <div className="answer">
              <h3>Answer</h3>
              <p className="answer-text">{answer.answer}</p>

              <h3>Sources</h3>

              {answer.sources?.length > 0 ? (
                <ul className="sources">
                  {answer.sources.map((source, index) => (
                    <li
                      key={`${source.source}-${source.page}-${index}`}
                    >
                      <span>📄</span>
                      <span>
                        {source.source} — Page {source.page}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="no-sources">
                  No relevant sources were found.
                </p>
              )}
            </div>
          )}
        </section>

        {error && <div className="error-message">{error}</div>}
      </main>

      <footer>
        Built with React, FastAPI, ChromaDB and Gemini
      </footer>
    </div>
  );
}

export default App;
