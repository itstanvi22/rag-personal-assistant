import { useState, useRef } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";

const API = process.env.REACT_APP_API_URL || "http://localhost:8001/api/v1";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const fileRef = useRef();
  const bottomRef = useRef();

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${API}/upload`, formData);
      setDocuments((prev) => [...prev, res.data]);
      setMessages((prev) => [
        ...prev,
        {
          role: "system",
          content: `✅ Uploaded "${res.data.filename}" — ${res.data.chunk_count} chunks indexed.`,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "system",
          content: `❌ Upload failed: ${err.response?.data?.detail || err.message}`,
        },
      ]);
    } finally {
      setUploading(false);
      fileRef.current.value = "";
    }
  };

  const handleChat = async () => {
    if (!query.trim()) return;
    if (documents.length === 0) {
      setMessages((prev) => [
        ...prev,
        { role: "system", content: "⚠️ Please upload a document first." },
      ]);
      return;
    }

    const userMessage = { role: "user", content: query };
    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setLoading(true);

    try {
      const res = await axios.post(`${API}/chat`, {
        query,
        document_ids: documents.map((d) => d.document_id),
        conversation_id: conversationId,
      });

      setConversationId(res.data.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.data.answer,
          citations: res.data.citations,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "system",
          content: `❌ Error: ${err.response?.data?.detail || err.message}`,
        },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleChat();
    }
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-64 bg-slate-900 border-r border-slate-700 flex flex-col p-4 gap-4">
        <h1 className="text-lg font-bold text-white">📚 RAG Assistant</h1>

        <button
          onClick={() => fileRef.current.click()}
          disabled={uploading}
          className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-3 py-2 rounded-lg disabled:opacity-50"
        >
          {uploading ? "Uploading..." : "Upload Document"}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.txt,.md"
          onChange={handleUpload}
          className="hidden"
        />

        <div className="flex flex-col gap-2">
          <p className="text-xs text-slate-400 uppercase tracking-wide">Uploaded</p>
          {documents.length === 0 && (
            <p className="text-xs text-slate-500">No documents yet</p>
          )}
          {documents.map((doc) => (
            <div key={doc.document_id} className="bg-slate-800 rounded p-2">
              <p className="text-xs text-white truncate">{doc.filename}</p>
              <p className="text-xs text-slate-400">{doc.chunk_count} chunks</p>
            </div>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex flex-col flex-1">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
          {messages.length === 0 && (
            <div className="text-center text-slate-500 mt-20">
              <p className="text-4xl mb-4">🧠</p>
              <p className="text-lg">Upload a document and start asking questions</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-2xl rounded-xl px-4 py-3 text-sm ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white"
                    : msg.role === "system"
                    ? "bg-slate-700 text-slate-300 text-xs"
                    : "bg-slate-800 text-slate-100"
                }`}
              >
                <ReactMarkdown>{msg.content}</ReactMarkdown>

                {/* Citations */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 border-t border-slate-600 pt-3">
                    <p className="text-xs text-slate-400 mb-2">Sources:</p>
                    {msg.citations.map((c, j) => (
                      <div key={j} className="bg-slate-900 rounded p-2 mb-1">
                        <p className="text-xs text-indigo-400 font-medium">
                          📄 {c.filename} — chunk {c.chunk_index}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">{c.chunk_text}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-800 rounded-xl px-4 py-3 text-sm text-slate-400">
                Thinking...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-slate-700 p-4 flex gap-3">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents... (Enter to send)"
            rows={2}
            className="flex-1 bg-slate-800 text-white rounded-lg px-4 py-2 text-sm resize-none border border-slate-600 focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={handleChat}
            disabled={loading || !query.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-lg text-sm disabled:opacity-50"
          >
            {loading ? "..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}