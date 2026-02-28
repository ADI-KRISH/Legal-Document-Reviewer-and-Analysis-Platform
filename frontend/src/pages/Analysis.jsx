import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { Header } from "../components/Header";
import { LoadingSpinner } from "../components/LoadingSpinner";
import "./Analysis.css";

const SAMPLE_QUERIES = [
    "What are the key risks in this contract?",
    "Summarize the termination clauses",
    "What are the parties' obligations?",
    "Are there any red flags or one-sided terms?",
];

export default function Analysis() {
    const { fileName } = useParams();
    const navigate = useNavigate();
    const name = decodeURIComponent(fileName);

    const [query, setQuery] = useState("");
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const analyse = async (q) => {
        const q2 = q || query;
        if (!q2.trim()) return;
        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const r = await api.getPlan(name, q2);
            setResult(r);
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const steps = result?.plan || [];

    return (
        <>
            <Header title="Document Analysis" subtitle={name} />
            <div className="page fade-up">
                <button className="btn btn-secondary btn-sm" style={{ marginBottom: "1.25rem" }} onClick={() => navigate("/documents")}>
                    ← Back
                </button>

                {/* Query input */}
                <div className="card analysis-card">
                    <h2 className="section-title">Ask the Orchestrator AI</h2>
                    <p style={{ color: "var(--text-2)", fontSize: "0.85rem", marginBottom: "1rem" }}>
                        The Orchestrator will plan and coordinate specialized agents to answer your question.
                    </p>
                    <div className="analysis-input-row">
                        <input
                            className="input"
                            placeholder="e.g. What are the key risks in this contract?"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && analyse()}
                        />
                        <button className="btn btn-primary" onClick={() => analyse()}>
                            Analyse →
                        </button>
                    </div>
                    <div className="sample-queries">
                        {SAMPLE_QUERIES.map((q) => (
                            <button key={q} className="sample-chip" onClick={() => { setQuery(q); analyse(q); }}>
                                {q}
                            </button>
                        ))}
                    </div>
                </div>

                {loading && (
                    <div className="card flex-center" style={{ padding: "3rem" }}>
                        <LoadingSpinner text="Orchestrator is planning and coordinating agents…" />
                    </div>
                )}

                {error && <div className="alert alert-error mt-2">⚠️ {error}</div>}

                {result && (
                    <div className="fade-up" style={{ marginTop: "1.25rem", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                        {/* Plan steps */}
                        {steps.length > 0 && (
                            <div className="card">
                                <h2 className="section-title">Execution Plan</h2>
                                <div className="plan-steps">
                                    {steps.map((step, i) => (
                                        <div key={i} className="step-card">
                                            <div className="step-num">{step.step ?? i + 1}</div>
                                            <div className="step-content">
                                                <div className="step-agent">
                                                    <span className="step-agent-icon">🤖</span>
                                                    {step.agent}
                                                </div>
                                                <div className="step-action">{step.action}</div>
                                                {step.reasoning && (
                                                    <div className="step-reason">💡 {step.reasoning}</div>
                                                )}
                                                {step.expected_output && (
                                                    <div className="step-output">Expected: {step.expected_output}</div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Raw response */}
                        <div className="card">
                            <h2 className="section-title">Full AI Response</h2>
                            <pre className="analysis-raw">{JSON.stringify(result, null, 2)}</pre>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
}
