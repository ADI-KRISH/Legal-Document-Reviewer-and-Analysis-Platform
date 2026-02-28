import { useState } from "react";
import { api } from "../api/client";
import { Header } from "../components/Header";
import { LoadingSpinner } from "../components/LoadingSpinner";
import "./Negotiate.css";

const SAMPLE_CLAUSES = {
    indemnity: "Each party shall indemnify and hold harmless the other party from any claims.",
    termination: "Either party may terminate this agreement with 30 days written notice.",
    liability: "In no event shall either party be liable for indirect or consequential damages.",
};

const SAMPLE_RISKS = {
    indemnity_risk: "Indemnity clause is overly broad and lacks mutual cap on liability.",
    termination_risk: "30-day notice period may be insufficient for complex transitions.",
};

export default function Negotiate() {
    const [clausesText, setClausesText] = useState(JSON.stringify(SAMPLE_CLAUSES, null, 2));
    const [risksText, setRisksText] = useState(JSON.stringify(SAMPLE_RISKS, null, 2));
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const negotiate = async () => {
        setLoading(true); setError(null); setResult(null);
        try {
            const clauses = JSON.parse(clausesText);
            const risks = JSON.parse(risksText);
            const r = await api.negotiate(clauses, risks);
            setResult(r);
        } catch (e) {
            setError(e.message || "Invalid JSON or request failed");
        } finally {
            setLoading(false);
        }
    };

    const resultText =
        result && typeof result === "object" && result.content
            ? result.content
            : typeof result === "string"
                ? result
                : JSON.stringify(result, null, 2);

    return (
        <>
            <Header title="Negotiation AI" subtitle="Get BATNA strategies and redline suggestions" />
            <div className="page fade-up">
                <div className="card neg-hero">
                    <div className="neg-hero-icon">⚖️</div>
                    <div>
                        <h2 className="neg-hero-title">Strategic Negotiation Engine</h2>
                        <p className="neg-hero-desc">
                            Provide the clauses and identified risks from your contract.
                            The AI will generate specific redlines, fallback positions, and BATNA strategies.
                        </p>
                    </div>
                </div>

                <div className="grid-2 mt-3">
                    <div className="card">
                        <label>📋 Contract Clauses <span style={{ color: "var(--text-3)", fontSize: "0.75rem" }}>(JSON)</span></label>
                        <textarea
                            className="textarea neg-textarea"
                            value={clausesText}
                            onChange={(e) => setClausesText(e.target.value)}
                            spellCheck={false}
                        />
                    </div>
                    <div className="card">
                        <label>🚨 Identified Risks <span style={{ color: "var(--text-3)", fontSize: "0.75rem" }}>(JSON)</span></label>
                        <textarea
                            className="textarea neg-textarea"
                            value={risksText}
                            onChange={(e) => setRisksText(e.target.value)}
                            spellCheck={false}
                        />
                    </div>
                </div>

                <button
                    className="btn btn-primary btn-lg neg-submit"
                    onClick={negotiate}
                    disabled={loading}
                >
                    {loading ? "Generating…" : "⚖️ Generate Negotiation Strategy"}
                </button>

                {loading && (
                    <div className="card flex-center" style={{ padding: "2.5rem" }}>
                        <LoadingSpinner text="AI is crafting your negotiation strategy…" />
                    </div>
                )}

                {error && <div className="alert alert-error mt-2">⚠️ {error}</div>}

                {result && !loading && (
                    <div className="card neg-result fade-up">
                        <div className="neg-result-header">
                            <h2 className="section-title" style={{ marginBottom: 0 }}>Negotiation Strategy</h2>
                            <span className="badge badge-info">AI Generated</span>
                        </div>
                        <hr className="divider" />
                        <div className="neg-result-body">{resultText}</div>
                    </div>
                )}
            </div>
        </>
    );
}
