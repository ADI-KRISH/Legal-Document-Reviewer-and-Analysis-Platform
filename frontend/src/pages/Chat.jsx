import { useState, useRef, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Header } from "../components/Header";
import "./Chat.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function ChatBubble({ msg }) {
    const isUser = msg.role === "user";
    return (
        <div className={`bubble-row ${isUser ? "bubble-row--user" : "bubble-row--ai"}`}>
            <div className={`bubble ${isUser ? "bubble--user" : "bubble--ai"}`}>
                <div className="bubble-text">{msg.text}</div>
                {msg.citations?.length > 0 && (
                    <div className="bubble-citations">
                        {msg.citations.map((c, i) => (
                            <span key={i} className="citation-chip">📎 {c}</span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default function Chat() {
    const { fileName } = useParams();
    const navigate = useNavigate();
    const name = decodeURIComponent(fileName || "");

    const [messages, setMessages] = useState([
        {
            role: "ai",
            text: `Hello! I'm your AI legal assistant. I've loaded **${name}** and I'm ready to answer your questions about it. Ask me anything!`,
            citations: [],
        },
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    const send = async () => {
        const q = input.trim();
        if (!q || loading) return;
        setInput("");
        setMessages((m) => [...m, { role: "user", text: q, citations: [] }]);
        setLoading(true);

        try {
            // QnA endpoint not yet on backend — use /plan as surrogate
            const res = await fetch(
                `${API_BASE}/plan/${encodeURIComponent(name)}/${encodeURIComponent(q)}`
            );
            const data = await res.json();
            const steps = data?.plan || [];
            const text =
                steps.length > 0
                    ? steps.map((s) => `[${s.agent}] ${s.action}`).join("\n")
                    : data?.res?.answer || JSON.stringify(data, null, 2);
            setMessages((m) => [
                ...m,
                { role: "ai", text, citations: data?.res?.citations || [] },
            ]);
        } catch (e) {
            setMessages((m) => [
                ...m,
                { role: "ai", text: `⚠️ Error: ${e.message}`, citations: [] },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const STARTERS = [
        "Who are the parties in this agreement?",
        "What is the governing law?",
        "What are the termination conditions?",
        "List all indemnity obligations.",
    ];

    return (
        <>
            <Header title="Document Chat" subtitle={name} />
            <div className="chat-layout">
                <div className="chat-sidebar-panel card">
                    <div className="chat-doc-info">
                        <div style={{ fontSize: "1.5rem" }}>📄</div>
                        <div>
                            <div className="chat-doc-name">{name}</div>
                            <div className="chat-doc-label">Active Document</div>
                        </div>
                    </div>
                    <hr className="divider" />
                    <div className="chat-starters-title">Suggested Questions</div>
                    {STARTERS.map((s) => (
                        <button key={s} className="chat-starter" onClick={() => { setInput(s); }}>
                            {s}
                        </button>
                    ))}
                    <hr className="divider" />
                    <button className="btn btn-secondary btn-sm" onClick={() => navigate("/documents")}>
                        ← Documents
                    </button>
                    <button className="btn btn-secondary btn-sm mt-1" onClick={() => navigate(`/summary/${encodeURIComponent(name)}`)}>
                        📝 Summary
                    </button>
                </div>

                <div className="chat-main">
                    <div className="chat-messages">
                        {messages.map((msg, i) => <ChatBubble key={i} msg={msg} />)}
                        {loading && (
                            <div className="bubble-row bubble-row--ai">
                                <div className="bubble bubble--ai bubble--typing">
                                    <span /><span /><span />
                                </div>
                            </div>
                        )}
                        <div ref={bottomRef} />
                    </div>

                    <div className="chat-input-bar">
                        <input
                            className="input chat-input"
                            placeholder="Ask a question about your document…"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && send()}
                            disabled={loading}
                        />
                        <button className="btn btn-primary chat-send" onClick={send} disabled={!input.trim() || loading}>
                            <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </>
    );
}
