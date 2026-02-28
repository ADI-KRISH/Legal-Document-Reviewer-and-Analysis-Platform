import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { Header } from "../components/Header";
import { LoadingSpinner } from "../components/LoadingSpinner";
import "./Documents.css";

export default function Documents() {
    const navigate = useNavigate();
    const [files, setFiles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = () => {
        setLoading(true);
        api.getFileList()
            .then((r) => { setFiles(r.files || []); setLoading(false); })
            .catch((e) => { setError(e.message); setLoading(false); });
    };

    useEffect(load, []);

    const ext = (name) => name.split(".").pop().toUpperCase();
    const extColor = { PDF: "#ef4444", TXT: "#22c55e", DOC: "#6366f1", DOCX: "#818cf8" };

    return (
        <>
            <Header title="My Documents" subtitle="All uploaded legal documents" />
            <div className="page fade-up">
                <div className="flex-between mb-top">
                    <div>
                        <span className="doc-count">{files.length}</span>
                        <span style={{ color: "var(--text-2)", fontSize: "0.875rem" }}> document{files.length !== 1 ? "s" : ""}</span>
                    </div>
                    <div className="flex gap-1">
                        <button className="btn btn-secondary btn-sm" onClick={load}>↻ Refresh</button>
                        <button className="btn btn-primary btn-sm" onClick={() => navigate("/upload")}>+ Upload</button>
                    </div>
                </div>

                {loading && (
                    <div className="flex-center" style={{ padding: "4rem" }}>
                        <LoadingSpinner text="Loading documents…" />
                    </div>
                )}

                {error && <div className="alert alert-error">⚠️ {error}</div>}

                {!loading && !error && files.length === 0 && (
                    <div className="empty-state card">
                        <span style={{ fontSize: "3rem" }}>📂</span>
                        <h3>No documents yet</h3>
                        <p>Upload your first legal document to get started.</p>
                        <button className="btn btn-primary mt-2" onClick={() => navigate("/upload")}>Upload Document</button>
                    </div>
                )}

                {!loading && files.length > 0 && (
                    <div className="doc-grid">
                        {files.map((f) => (
                            <div key={f} className="doc-card card">
                                <div className="doc-card-header">
                                    <div className="doc-ext-badge" style={{ background: (extColor[ext(f)] || "#6366f1") + "22", color: extColor[ext(f)] || "#818cf8" }}>
                                        {ext(f)}
                                    </div>
                                </div>
                                <div className="doc-name" title={f}>{f}</div>
                                <div className="doc-actions">
                                    <button
                                        className="btn btn-secondary btn-sm"
                                        onClick={() => navigate(`/summary/${encodeURIComponent(f)}`)}
                                    >
                                        📝 Summary
                                    </button>
                                    <button
                                        className="btn btn-secondary btn-sm"
                                        onClick={() => navigate(`/analysis/${encodeURIComponent(f)}`)}
                                    >
                                        🔍 Analyse
                                    </button>
                                    <button
                                        className="btn btn-secondary btn-sm"
                                        onClick={() => navigate(`/chat/${encodeURIComponent(f)}`)}
                                    >
                                        💬 Chat
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </>
    );
}
