
import { useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

export default function App() {
  const [file, setFile] = useState(null);
  const [documentId, setDocumentId] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function uploadDocument() {
    if (!file) {
      setError("Please select a PDF or JSON file.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API}/documents`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Upload failed.");
      }

      setDocumentId(data.document_id);
      setSessionId("");
      setMessages([]);
    } catch (err) {
      setError(err.message || "Could not connect to the backend.");
    } finally {
      setLoading(false);
    }
  }

  async function sendQuestion(event) {
    event.preventDefault();
    if (!question.trim() || !documentId || loading) return;

    const currentQuestion = question.trim();
    setQuestion("");
    setError("");
    setMessages((old) => [
      ...old,
      { role: "user", content: currentQuestion },
    ]);
    setLoading(true);

    try {
      const response = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: documentId,
          session_id: sessionId || null,
          question: currentQuestion,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Question failed.");
      }

      setSessionId(data.session_id);
      setMessages((old) => [
        ...old,
        {
          role: "assistant",
          content: data.answer,
          citations: data.citations || [],
        },
      ]);
    } catch (err) {
      setError(err.message || "Could not connect to the backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app">
      <header className="topbar">
        <div className="brand-icon">Z</div>
        <div>
          <h1>Zania QA</h1>
          <p>Ask questions about your documents</p>
        </div>
        <span className="status">AI DOCUMENT CHAT</span>
      </header>

      <section className="workspace">
        <aside className="sidebar">
          <h2>Your document</h2>
          <p className="muted">
            Upload a PDF or JSON file to start a conversation.
          </p>

          <label className="upload-area">
            <span className="upload-icon">↑</span>
            <strong>Choose a file</strong>
            <span className="muted">PDF or JSON, up to 10 MB</span>
            <input
              type="file"
              accept=".pdf,.json,application/pdf,application/json"
              onChange={(event) => {
                setFile(event.target.files?.[0] || null);
                setDocumentId("");
                setSessionId("");
                setMessages([]);
                setError("");
              }}
            />
          </label>

          {file && <p className="filename">📄 {file.name}</p>}

          <button
            className="primary-button"
            onClick={uploadDocument}
            disabled={!file || loading}
          >
            {loading && !documentId ? "Uploading..." : "Upload document"}
          </button>

          {documentId && (
            <div className="success">
              <span>✓</span>
              <div>
                <strong>Document ready</strong>
                <p>You can start asking questions.</p>
              </div>
            </div>
          )}

          <div className="sidebar-note">
            <strong>Privacy tip</strong>
            <p>Only upload documents you're authorized to share.</p>
          </div>
        </aside>

        <section className="chat-panel">
          <div className="chat-heading">
            <div>
              <h2>Document assistant</h2>
              <p className="muted">
                {documentId
                  ? "Ask a question about your uploaded document."
                  : "Upload a document to begin."}
              </p>
            </div>
            <span className={documentId ? "dot active" : "dot"} />
          </div>

          <div className="messages">
            {messages.length === 0 && (
              <div className="welcome">
                <div className="welcome-icon">✳</div>
                <h2>Your document, explained.</h2>
                <p>
                  Upload a document and ask questions. Answers will appear
                  here with source references when available.
                </p>
                <div className="suggestion">
                  “Summarize the main findings”
                </div>
                <div className="suggestion">
                  “What are the key takeaways?”
                </div>
              </div>
            )}

            {messages.map((message, index) => (
              <article
                className={`message ${message.role}`}
                key={`${index}-${message.role}`}
              >
                <div className="message-label">
                  {message.role === "user" ? "You" : "Zania AI"}
                </div>
                <div className="message-content">{message.content}</div>

                {message.citations?.length > 0 && (
                  <div className="citations">
                    <strong>Sources</strong>
                    {message.citations.map((citation, i) => (
                      <span key={`${citation.source}-${citation.page}-${i}`}>
                        {citation.source || "Document"}
                        {citation.page != null
                          ? ` · Page ${citation.page}`
                          : ""}
                      </span>
                    ))}
                  </div>
                )}
              </article>
            ))}

            {loading && documentId && (
              <div className="thinking">Thinking…</div>
            )}
          </div>

          {error && <div className="error">{error}</div>}

          <form className="question-form" onSubmit={sendQuestion}>
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder={
                documentId
                  ? "Ask a question about your document..."
                  : "Upload a document to start chatting"
              }
              disabled={!documentId || loading}
            />
            <button
              type="submit"
              disabled={!documentId || !question.trim() || loading}
            >
              Send ↑
            </button>
          </form>

          <p className="footer-note">
            AI-generated answers may be inaccurate. Verify important details
            against the original document.
          </p>
        </section>
      </section>
    </main>
  );
}