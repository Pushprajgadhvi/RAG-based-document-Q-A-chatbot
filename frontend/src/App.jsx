import { useState, useEffect } from "react";
import ChatWindow from "./components/ChatWindow";
import DocumentUploader from "./components/DocumentUploader";
import Sidebar from "./components/Sidebar";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionReady, setSessionReady] = useState(false);
  const [error, setError] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);

  useEffect(() => {
    initSession();
  }, []);

  const initSession = async () => {
    try {
      const res = await fetch(`${API_BASE}/session/new`, { method: "POST" });
      const data = await res.json();
      setSessionId(data.session_id);
      setSessionReady(true);
      setMessages([{
        role: "assistant",
        content: "👋 Hello! I'm your RAG Assistant. Upload your documents to get started.",
        sources: [],
      }]);
    } catch (err) {
      setError("Cannot connect to backend. Make sure it's running.");
    }
  };

  const handleUpload = async (file) => {
    if (!sessionId) return;
    setIsLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/upload/${sessionId}`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");

      setDocuments((prev) => [...prev, { name: data.filename, chunks: data.chunks_added }]);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `✅ **"${data.filename}"** uploaded and processed into **${data.chunks_added} chunks**. You can now ask questions!`,
          sources: [],
        },
      ]);
      setShowUploadModal(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuestion = async (question) => {
    if (!sessionId || !question.trim()) return;
    setMessages((prev) => [...prev, { role: "user", content: question, sources: [] }]);
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, question }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Chat failed");
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer, sources: data.sources }]);
    } catch (err) {
      setError(err.message);
      setMessages((prev) => [...prev, { role: "assistant", content: `❌ Error: ${err.message}`, sources: [] }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    if (!sessionId) return;
    try {
      await fetch(`${API_BASE}/session/${sessionId}`, { method: "DELETE" });
      setDocuments([]);
      setMessages([{
        role: "assistant",
        content: "Session cleared! Upload a new document to start again.",
        sources: [],
      }]);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        documents={documents}
        sessionId={sessionId}
        onReset={handleReset}
        sessionReady={sessionReady}
      />

      <main className="main-content">
        <header className="app-header">
          <div className="header-left">
            <h2 className="model-name">RAG Assistant <span className="version">v1.0</span></h2>
          </div>
          <div className="header-right">
            <button 
              className="upload-trigger-btn"
              onClick={() => setShowUploadModal(true)}
              disabled={!sessionReady}
            >
              <span className="icon">📤</span> Upload
            </button>
            <div className={`status-indicator ${sessionReady ? 'online' : 'offline'}`}>
              {sessionReady ? 'Connected' : 'Disconnected'}
            </div>
          </div>
        </header>

        {error && (
          <div className="error-toast">
            <span>{error}</span>
            <button onClick={() => setError(null)}>✕</button>
          </div>
        )}

        <ChatWindow
          messages={messages}
          onSend={handleQuestion}
          isLoading={isLoading}
          disabled={documents.length === 0 || !sessionReady}
        />

        {showUploadModal && (
          <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
              <div className="modal-header">
                <h3>Knowledge Base</h3>
                <button className="close-btn" onClick={() => setShowUploadModal(false)}>✕</button>
              </div>
              <DocumentUploader
                onUpload={handleUpload}
                isLoading={isLoading}
                disabled={!sessionReady}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
