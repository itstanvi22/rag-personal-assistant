import { useState, useRef } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";

const API = "http://localhost:8001/api/v1";

const CHANGE_TYPES = [
  { value: "general", label: "General" },
  { value: "policy_update", label: "Policy Update" },
  { value: "process_change", label: "Process Change" },
  { value: "system_migration", label: "System Migration" },
  { value: "organizational_restructure", label: "Org Restructure" },
  { value: "compliance_update", label: "Compliance Update" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("chat");
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [changeType, setChangeType] = useState("general");
  const [changeTitle, setChangeTitle] = useState("");
  const [departments, setDepartments] = useState("");
  const [faqs, setFaqs] = useState(null);
  const [impactData, setImpactData] = useState(null);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [icmsLoading, setIcmsLoading] = useState(false);
  const fileRef = useRef();
  const bottomRef = useRef();

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("change_type", changeType);
    formData.append("change_title", changeTitle || file.name);
    formData.append("affected_departments", departments);

    try {
      const res = await axios.post(`${API}/upload`, formData);
      setDocuments((prev) => [...prev, res.data]);
      setMessages((prev) => [
        ...prev,
        {
          role: "system",
          content: `✅ Uploaded "${res.data.filename}" as [${res.data.change_type}] — ${res.data.chunk_count} chunks indexed.`,
        },
      ]);
      setChangeTitle("");
      setDepartments("");
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

  const handleGenerateFAQ = async (docId) => {
    setSelectedDocId(docId);
    setIcmsLoading(true);
    setFaqs(null);
    setImpactData(null);
    setActiveTab("icms");

    try {
      const res = await axios.post(`${API}/icms/generate-faq`, {
        document_id: docId,
        num_questions: 10,
      });
      setFaqs(res.data);
    } catch (err) {
      alert(`FAQ generation failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIcmsLoading(false);
    }
  };

  const handleAnalyzeImpact = async (docId) => {
    setSelectedDocId(docId);
    setIcmsLoading(true);
    setFaqs(null);
    setImpactData(null);
    setActiveTab("icms");

    try {
      const res = await axios.post(`${API}/icms/analyze-impact`, {
        document_id: docId,
      });
      setImpactData(res.data);
    } catch (err) {
      alert(`Impact analysis failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIcmsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleChat();
    }
  };

  const categoryColors = {
    Timeline: "bg-blue-900 text-blue-300",
    Process: "bg-green-900 text-green-300",
    Impact: "bg-orange-900 text-orange-300",
    Policy: "bg-purple-900 text-purple-300",
    General: "bg-slate-700 text-slate-300",
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-72 bg-slate-900 border-r border-slate-700 flex flex-col p-4 gap-4 overflow-y-auto">
        <h1 className="text-lg font-bold text-white">📚 RAG + ICMS</h1>

        {/* Upload section */}
        <div className="flex flex-col gap-2">
          <p className="text-xs text-slate-400 uppercase tracking-wide">Upload Document</p>

          <select
            value={changeType}
            onChange={(e) => setChangeType(e.target.value)}
            className="bg-slate-800 text-white text-xs rounded px-2 py-1 border border-slate-600"
          >
            {CHANGE_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>

          <input
            type="text"
            placeholder="Change title (optional)"
            value={changeTitle}
            onChange={(e) => setChangeTitle(e.target.value)}
            className="bg-slate-800 text-white text-xs rounded px-2 py-1 border border-slate-600 placeholder-slate-500"
          />

          <input
            type="text"
            placeholder="Departments (comma separated)"
            value={departments}
            onChange={(e) => setDepartments(e.target.value)}
            className="bg-slate-800 text-white text-xs rounded px-2 py-1 border border-slate-600 placeholder-slate-500"
          />

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
        </div>

        {/* Document list */}
        <div className="flex flex-col gap-2">
          <p className="text-xs text-slate-400 uppercase tracking-wide">Documents</p>
          {documents.length === 0 && (
            <p className="text-xs text-slate-500">No documents yet</p>
          )}
          {documents.map((doc) => (
            <div key={doc.document_id} className="bg-slate-800 rounded p-2 flex flex-col gap-1">
              <p className="text-xs text-white truncate">{doc.filename}</p>
              <p className="text-xs text-slate-400">{doc.change_type} · {doc.chunk_count} chunks</p>
              <div className="flex gap-1 mt-1">
                <button
                  onClick={() => handleGenerateFAQ(doc.document_id)}
                  className="text-xs bg-indigo-700 hover:bg-indigo-600 text-white px-2 py-1 rounded flex-1"
                >
                  FAQ
                </button>
                <button
                  onClick={() => handleAnalyzeImpact(doc.document_id)}
                  className="text-xs bg-emerald-700 hover:bg-emerald-600 text-white px-2 py-1 rounded flex-1"
                >
                  Impact
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main area */}
      <div className="flex flex-col flex-1">
        {/* Tabs */}
        <div className="flex border-b border-slate-700 bg-slate-900">
          {["chat", "icms"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 text-sm font-medium ${
                activeTab === tab
                  ? "text-white border-b-2 border-indigo-500"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {tab === "chat" ? "💬 Chat" : "🔄 Change Intelligence"}
            </button>
          ))}
        </div>

        {/* Chat Tab */}
        {activeTab === "chat" && (
          <div className="flex flex-col flex-1">
            <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
              {messages.length === 0 && (
                <div className="text-center text-slate-500 mt-20">
                  <p className="text-4xl mb-4">🧠</p>
                  <p className="text-lg">Upload a document and start asking questions</p>
                </div>
              )}
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-2xl rounded-xl px-4 py-3 text-sm ${
                    msg.role === "user"
                      ? "bg-indigo-600 text-white"
                      : msg.role === "system"
                      ? "bg-slate-700 text-slate-300 text-xs"
                      : "bg-slate-800 text-slate-100"
                  }`}>
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
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
        )}

        {/* ICMS Tab */}
        {activeTab === "icms" && (
          <div className="flex-1 overflow-y-auto p-6">
            {icmsLoading && (
              <div className="text-center text-slate-400 mt-20">
                <p className="text-4xl mb-4 animate-spin">⚙️</p>
                <p>Analyzing document with AI...</p>
              </div>
            )}

            {!icmsLoading && !faqs && !impactData && (
              <div className="text-center text-slate-500 mt-20">
                <p className="text-4xl mb-4">🔄</p>
                <p className="text-lg">Select a document from the sidebar</p>
                <p className="text-sm mt-2">Click FAQ or Impact to analyze</p>
              </div>
            )}

            {/* FAQ Display */}
            {faqs && (
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-white">{faqs.change_title}</h2>
                    <p className="text-sm text-slate-400 mt-1">
                      {faqs.total_faqs} FAQs generated · {faqs.change_type} · {faqs.affected_departments}
                    </p>
                  </div>
                  <button
                    onClick={() => handleAnalyzeImpact(selectedDocId)}
                    className="bg-emerald-700 hover:bg-emerald-600 text-white text-sm px-4 py-2 rounded-lg"
                  >
                    View Impact Analysis
                  </button>
                </div>

                <div className="grid gap-3">
                  {faqs.faqs.map((faq, i) => (
                    <div key={i} className="bg-slate-800 rounded-xl p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <p className="text-white font-medium text-sm">Q: {faq.question}</p>
                          <p className="text-slate-300 text-sm mt-2">A: {faq.answer}</p>
                        </div>
                        <span className={`text-xs px-2 py-1 rounded-full whitespace-nowrap ${categoryColors[faq.category] || categoryColors.General}`}>
                          {faq.category}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Impact Analysis Display */}
            {impactData && (
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold text-white">
                    Impact Analysis: {impactData.change_title}
                  </h2>
                  <button
                    onClick={() => handleGenerateFAQ(selectedDocId)}
                    className="bg-indigo-700 hover:bg-indigo-600 text-white text-sm px-4 py-2 rounded-lg"
                  >
                    Generate FAQ
                  </button>
                </div>

                {impactData.impact_assessment && (
                  <div className="grid gap-4">
                    {/* Summary */}
                    <div className="bg-slate-800 rounded-xl p-4">
                      <p className="text-xs text-slate-400 uppercase mb-2">Summary</p>
                      <p className="text-slate-200 text-sm">{impactData.impact_assessment.summary}</p>
                    </div>

                    {/* Risk Level */}
                    <div className="bg-slate-800 rounded-xl p-4">
                      <p className="text-xs text-slate-400 uppercase mb-2">Risk Level</p>
                      <span className={`text-sm font-bold px-3 py-1 rounded-full ${
                        impactData.impact_assessment.risk_level === "High"
                          ? "bg-red-900 text-red-300"
                          : impactData.impact_assessment.risk_level === "Medium"
                          ? "bg-yellow-900 text-yellow-300"
                          : "bg-green-900 text-green-300"
                      }`}>
                        {impactData.impact_assessment.risk_level}
                      </span>
                      <p className="text-slate-400 text-xs mt-2">{impactData.impact_assessment.risk_reason}</p>
                    </div>

                    {/* Three column grid */}
                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-slate-800 rounded-xl p-4">
                        <p className="text-xs text-slate-400 uppercase mb-2">Key Changes</p>
                        <ul className="text-sm text-slate-300 flex flex-col gap-1">
                          {(impactData.impact_assessment.key_changes || []).map((c, i) => (
                            <li key={i} className="flex gap-2"><span className="text-indigo-400">•</span>{c}</li>
                          ))}
                        </ul>
                      </div>

                      <div className="bg-slate-800 rounded-xl p-4">
                        <p className="text-xs text-slate-400 uppercase mb-2">Who is Affected</p>
                        <ul className="text-sm text-slate-300 flex flex-col gap-1">
                          {(impactData.impact_assessment.who_is_affected || []).map((w, i) => (
                            <li key={i} className="flex gap-2"><span className="text-emerald-400">•</span>{w}</li>
                          ))}
                        </ul>
                      </div>

                      <div className="bg-slate-800 rounded-xl p-4">
                        <p className="text-xs text-slate-400 uppercase mb-2">Actions Required</p>
                        <ul className="text-sm text-slate-300 flex flex-col gap-1">
                          {(impactData.impact_assessment.action_required || []).map((a, i) => (
                            <li key={i} className="flex gap-2"><span className="text-orange-400">•</span>{a}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Timeline */}
                    {impactData.impact_assessment.timeline && (
                      <div className="bg-slate-800 rounded-xl p-4">
                        <p className="text-xs text-slate-400 uppercase mb-2">Timeline</p>
                        <p className="text-slate-200 text-sm">{impactData.impact_assessment.timeline}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}