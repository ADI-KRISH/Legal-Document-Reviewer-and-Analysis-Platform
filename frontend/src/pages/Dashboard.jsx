import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { Header } from "../components/Header";
import "./Dashboard.css";

const QUICK_ACTIONS = [
    { label: "Upload Document", to: "/upload", icon: "📤", color: "#6366f1" },
    { label: "My Documents", to: "/documents", icon: "📂", color: "#22c55e" },
    { label: "Negotiate", to: "/negotiate", icon: "⚖️", color: "#f59e0b" },
];

const FEATURES = [
    { icon: "🔍", title: "Clause Extraction", desc: "Automatic parsing of parties, termination, indemnity, and more into structured JSON." },
    { icon: "🚨", title: "Risk Detection", desc: "Red-flag engine spots overly broad or non-standard clauses using industry playbooks." },
    { icon: "🤝", title: "Negotiation AI", desc: "Generates BATNA redlines and fallback positions to protect your interests." },
    { icon: "📚", title: "Legal Research RAG", desc: "Cites actual case law and statutes when answering document questions." },
    { icon: "📝", title: "Smart Summaries", desc: "200-word executive summaries covering parties, purpose, and key terms." },
    { icon: "💬", title: "Document Q&A", desc: "Chat with your contract—grounded answers with chunk-level citations." },
];

export default function Dashboard() {
    const navigate = useNavigate();
    const [docCount, setDocCount] = useState(null);
    const [backendOk, setBackendOk] = useState(null);

    useEffect(() => {
        api.health()
            .then(() => setBackendOk(true))
            .catch(() => setBackendOk(false));
        api.getFileList()
            .then((r) => setDocCount(r.files?.length ?? 0))
            .catch(() => setDocCount(0));
    }, []);

    return (
        <>
            <Header title="Dashboard" subtitle="Legal Document Intelligence Platform" />
            <div className="page fade-up">
                {/* Hero */}
                <div className="dash-hero">
                    <div className="dash-hero-badge">AI Legal Counsel</div>
                    <h1 className="dash-hero-title">
                        Your AI-Powered
                        <br />
                        <span className="dash-hero-accent">Legal Advisor</span>
                    </h1>
                    <p className="dash-hero-desc">
                        Upload contracts, NDAs, employment agreements and let multi-agent AI extract clauses,
                        detect risks, suggest negotiation strategies—in seconds.
                    </p>
                    <div className="dash-hero-actions">
                        <button className="btn btn-primary btn-lg" onClick={() => navigate("/upload")}>
                            <span>📤</span> Upload Document
                        </button>
                        <button className="btn btn-secondary btn-lg" onClick={() => navigate("/documents")}>
                            View Documents
                        </button>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid-3 mt-4">
                    <StatCard
                        icon="📄"
                        label="Documents Uploaded"
                        value={docCount ?? "—"}
                        color="var(--accent)"
                    />
                    <StatCard
                        icon="🟢"
                        label="Backend Status"
                        value={backendOk === null ? "Checking…" : backendOk ? "Online" : "Offline"}
                        color={backendOk ? "var(--success)" : "var(--danger)"}
                    />
                    <StatCard
                        icon="🤖"
                        label="AI Agents Active"
                        value="6"
                        color="var(--warning)"
                    />
                </div>

                {/* Quick actions */}
                <h2 className="section-title mt-4">Quick Actions</h2>
                <div className="grid-3">
                    {QUICK_ACTIONS.map((a) => (
                        <button key={a.to} className="dash-action card" onClick={() => navigate(a.to)}>
                            <span className="dash-action-icon" style={{ background: a.color + "22", color: a.color }}>
                                {a.icon}
                            </span>
                            <span className="dash-action-label">{a.label}</span>
                            <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} style={{ color: "var(--text-3)" }}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                            </svg>
                        </button>
                    ))}
                </div>

                {/* Features */}
                <h2 className="section-title mt-4">Platform Capabilities</h2>
                <div className="grid-3">
                    {FEATURES.map((f) => (
                        <div key={f.title} className="card dash-feature">
                            <div className="dash-feature-icon">{f.icon}</div>
                            <div className="dash-feature-title">{f.title}</div>
                            <div className="dash-feature-desc">{f.desc}</div>
                        </div>
                    ))}
                </div>

                {/* Agent Architecture */}
                <div className="card mt-4 dash-arch">
                    <h2 className="section-title" style={{ marginBottom: "1.5rem" }}>Agent Architecture</h2>
                    <div className="arch-flow">
                        {["Orchestrator", "Clause Extraction", "Risk Engine", "Negotiation AI", "Q&A RAG", "Summariser"].map(
                            (a, i, arr) => (
                                <div key={a} className="arch-item">
                                    <div className="arch-node">{a}</div>
                                    {i < arr.length - 1 && <div className="arch-arrow">→</div>}
                                </div>
                            )
                        )}
                    </div>
                </div>
            </div>
        </>
    );
}

function StatCard({ icon, label, value, color }) {
    return (
        <div className="card stat-card">
            <div className="stat-icon" style={{ color }}>{icon}</div>
            <div className="stat-value" style={{ color }}>{value}</div>
            <div className="stat-label">{label}</div>
        </div>
    );
}
