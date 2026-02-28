import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { Header } from "../components/Header";
import { LoadingSpinner } from "../components/LoadingSpinner";
import "./Summary.css";

export default function Summary() {
    const { fileName } = useParams();
    const navigate = useNavigate();
    const name = decodeURIComponent(fileName);

    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const load = () => {
        setLoading(true);
        setError(null);
        api.getSummary(name)
            .then((r) => { setSummary(r.summary); setLoading(false); })
            .catch((e) => { setError(e.message); setLoading(false); });
    };

    useEffect(load, [name]);

    // Extract text from LangChain AIMessage object if needed
    const summaryText =
        summary && typeof summary === "object" && summary.content
            ? summary.content
            : typeof summary === "string"
                ? summary
                : JSON.stringify(summary, null, 2);

    return (
        <>
            <Header title="Document Summary" subtitle={name} />
            <div className="page fade-up">
                <div className="summary-back">
                    <button className="btn btn-secondary btn-sm" onClick={() => navigate("/documents")}>
                        ← Back to Documents
                    </button>
                    <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/analysis/${encodeURIComponent(name)}`)}>
                        🔍 Full Analysis →
                    </button>
                    <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/chat/${encodeURIComponent(name)}`)}>
                        💬 Chat →
                    </button>
                </div>

                <div className="summary-doc-card card">
                    <div className="summary-doc-icon">📄</div>
                    <div>
                        <div className="summary-doc-name">{name}</div>
                        <div className="summary-doc-label">Legal Document</div>
                    </div>
                </div>

                <div className="card summary-card">
                    <div className="summary-header">
                        <h2 className="section-title" style={{ marginBottom: 0 }}>AI-Generated Summary</h2>
                        <button className="btn btn-secondary btn-sm" onClick={load}>↻ Refresh</button>
                    </div>
                    <hr className="divider" />

                    {loading && (
                        <div className="flex-center" style={{ padding: "3rem" }}>
                            <LoadingSpinner text="AI is summarizing your document…" />
                        </div>
                    )}

                    {error && <div className="alert alert-error">⚠️ {error}</div>}

                    {!loading && !error && summaryText && (
                        <div className="summary-body">{summaryText}</div>
                    )}

                    {!loading && !error && !summaryText && (
                        <div className="empty-state">
                            <span>📭</span>
                            <p>No summary available. The document may still be processing.</p>
                            <button className="btn btn-primary mt-2" onClick={load}>Try Again</button>
                        </div>
                    )}
                </div>

                <div className="summary-next card">
                    <h3 className="section-title">Continue Analysis</h3>
                    <div className="flex gap-2" style={{ flexWrap: "wrap" }}>
                        <button className="btn btn-primary" onClick={() => navigate(`/analysis/${encodeURIComponent(name)}`)}>
                            🔍 Run Full Analysis
                        </button>
                        <button className="btn btn-secondary" onClick={() => navigate("/negotiate")}>
                            ⚖️ Start Negotiation
                        </button>
                        <button className="btn btn-secondary" onClick={() => navigate(`/chat/${encodeURIComponent(name)}`)}>
                            💬 Ask Questions
                        </button>
                    </div>
                </div>
            </div>
        </>
    );
}
