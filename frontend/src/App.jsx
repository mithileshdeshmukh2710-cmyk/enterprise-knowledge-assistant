import { useState, useEffect } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";

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
  }

  async function loadDocuments() {
    try {
      const response = await fetch(`${API_URL}/documents`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not load documents.");
      }

      setDocuments(data.documents);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(filename) {
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
      await loadDocuments();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="brand-icon">✦</span>
          <span>KnowledgeAI</span>
        </div>
        <span className="header-label">Enterprise Knowledge Assistant</span>
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
            {uploading ? "Indexing document..." : "Upload and index"}
          </button>

          {uploadMessage && (
            <div className="success-message">
              ✓ {uploadMessage}
            </div>
          )}
        </section>

        <section className="panel">
          <div className="section-heading">
            <span className="step">02</span>
            <div>
              <h2>Knowledge base</h2>
              <p>Your indexed documents.</p>
            </div>
          </div>

          <button
            className="secondary-button"
            onClick={loadDocuments}
          >
            Refresh documents
          </button>

          {documents.length === 0 ? (
            <p className="no-sources">No documents indexed yet.</p>
          ) : (
            <ul className="document-list">
              {documents.map((doc) => (
                <li key={doc.filename}>
                  <div>
                    <strong>{doc.filename}</strong>
                    <p>{doc.pages} pages · {doc.chunks} chunks</p>
                  </div>

                  <button
                    className="delete-button"
                    onClick={() => handleDelete(doc.filename)}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="panel">
          <div className="section-heading">
            <span className="step">03</span>
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

              {answer.sources.length > 0 ? (
                <ul className="sources">
                  {answer.sources.map((source, index) => (
                    <li key={`${source.source}-${source.page}-${index}`}>
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
