import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { Header } from "../components/Header";
import { LoadingSpinner } from "../components/LoadingSpinner";
import "./Upload.css";

const ACCEPTED = [".pdf", ".txt", ".doc", ".docx"];

export default function Upload() {
    const navigate = useNavigate();
    const [dragging, setDragging] = useState(false);
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState(null); // null | 'uploading' | 'success' | 'error'
    const [message, setMessage] = useState("");

    const onDrop = useCallback((e) => {
        e.preventDefault();
        setDragging(false);
        const f = e.dataTransfer?.files?.[0] || e.target?.files?.[0];
        if (f) setFile(f);
    }, []);

    const upload = async () => {
        if (!file) return;
        setStatus("uploading");
        setMessage("");
        try {
            const res = await api.uploadFile(file);
            setStatus("success");
            setMessage(res.message || "File uploaded successfully.");
        } catch (err) {
            setStatus("error");
            setMessage(err.message || "Upload failed.");
        }
    };

    const reset = () => { setFile(null); setStatus(null); setMessage(""); };

    return (
        <>
            <Header title="Upload Document" subtitle="Upload a legal document for AI analysis" />
            <div className="page fade-up">
                <div className="upload-wrapper">

                    {/* Drop zone */}
                    {!file && (
                        <label
                            className={`drop-zone card ${dragging ? "drop-zone--active" : ""}`}
                            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                            onDragLeave={() => setDragging(false)}
                            onDrop={onDrop}
                        >
                            <input type="file" accept={ACCEPTED.join(",")} onChange={onDrop} hidden />
                            <div className="drop-icon">📄</div>
                            <p className="drop-title">Drop your document here</p>
                            <p className="drop-sub">or <span className="drop-link">browse files</span></p>
                            <p className="drop-formats">Supported: PDF, TXT, DOC, DOCX</p>
                        </label>
                    )}

                    {/* Preview selected file */}
                    {file && status !== "success" && (
                        <div className="card file-preview">
                            <div className="file-preview-icon">📄</div>
                            <div className="file-preview-info">
                                <div className="file-preview-name">{file.name}</div>
                                <div className="file-preview-size">{(file.size / 1024).toFixed(1)} KB</div>
                            </div>
                            <button className="btn btn-secondary btn-sm" onClick={reset}>Remove</button>
                        </div>
                    )}

                    {/* Progress / Status */}
                    {status === "uploading" && (
                        <div className="card upload-status">
                            <LoadingSpinner text="Uploading and queuing for AI processing…" />
                        </div>
                    )}

                    {status === "success" && (
                        <div className="card upload-success">
                            <div className="success-icon">✅</div>
                            <h2 className="success-title">Upload Successful!</h2>
                            <p className="success-msg">{message}</p>
                            <p className="success-msg" style={{ marginTop: "0.3rem", color: "var(--text-3)", fontSize: "0.8rem" }}>
                                Background AI agents are now processing your document.
                            </p>
                            <div className="success-actions">
                                <button className="btn btn-primary" onClick={() => navigate("/documents")}>
                                    View Documents
                                </button>
                                <button className="btn btn-secondary" onClick={reset}>
                                    Upload Another
                                </button>
                            </div>
                        </div>
                    )}

                    {status === "error" && (
                        <div className="alert alert-error mt-2">
                            ⚠️ {message}
                        </div>
                    )}

                    {/* Upload button */}
                    {file && status !== "uploading" && status !== "success" && (
                        <button className="btn btn-primary btn-lg upload-btn" onClick={upload}>
                            <span>🚀</span> Upload & Analyse
                        </button>
                    )}

                    {/* Tips */}
                    <div className="upload-tips card">
                        <h3 className="section-title">What happens next?</h3>
                        <div className="tips-list">
                            {[
                                { n: "1", t: "Document Ingestion", d: "Your file is securely stored and chunked for vector search." },
                                { n: "2", t: "Clause Extraction", d: "AI identifies parties, termination clauses, indemnity terms, and more." },
                                { n: "3", t: "Risk Analysis", d: "Red-flag engine runs against industry playbooks to detect issues." },
                                { n: "4", t: "Summary Generation", d: "A concise executive summary is generated for review." },
                            ].map((tip) => (
                                <div key={tip.n} className="tip-item">
                                    <div className="tip-num">{tip.n}</div>
                                    <div>
                                        <div className="tip-title">{tip.t}</div>
                                        <div className="tip-desc">{tip.d}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                </div>
            </div>
        </>
    );
}
