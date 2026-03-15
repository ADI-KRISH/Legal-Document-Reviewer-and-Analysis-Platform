"""
Workflow Test for the Legal Document Agentic System
====================================================
Tests the graph structure and routing logic WITHOUT hitting real LLMs or databases.
Uses mock agent functions so you can validate the workflow independently.

Run from backend/ with venv activated:
    python -m system.test.test_workflow

Or from backend/system/test/:
    python test_workflow.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# ── Colour helpers ─────────────────────────────────────────────────────────────
G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"; C = "\033[96m"; B = "\033[1m"; X = "\033[0m"
ok   = lambda s: print(f"  {G}✅ {s}{X}")
fail = lambda s: print(f"  {R}❌ {s}{X}")
info = lambda s: print(f"  {C}ℹ  {s}{X}")
head = lambda s: print(f"\n{B}{C}{'─'*55}\n  {s}\n{'─'*55}{X}")


# ══════════════════════════════════════════════════════════
# TEST 1 — Graph compiles
# ══════════════════════════════════════════════════════════
def test_graph_compiles():
    head("TEST 1 — Graph compiles")
    try:
        from system.state import build_graph
        graph = build_graph()
        assert graph is not None
        ok("Graph compiled and is not None")
        nodes = list(graph.nodes)
        info(f"Nodes found: {nodes}")

        expected = [
            "Orchestrator",
            "clause_extraction_agent",
            "risk_analyser",
            "report_generator",
            "QnA_Agent",
            "negotiation_agent",
            "research_agent",
        ]
        for n in expected:
            if n in nodes:
                ok(f"Node present: {n}")
            else:
                fail(f"Node MISSING: {n}")
        return graph
    except Exception as e:
        fail(f"Graph failed to compile: {e}")
        import traceback; traceback.print_exc()
        return None


# ══════════════════════════════════════════════════════════
# TEST 2 — SharedState can be instantiated
# ══════════════════════════════════════════════════════════
def test_shared_state():
    head("TEST 2 — SharedState structure")
    try:
        from system.state import SharedState
        sample: SharedState = {
            "document_uploaded": True,
            "file_name": ["sample_nda.txt"],
            "results": [],
            "messages": [],
            "negotiation_json": {},
            "risk_json": {},
            "clauses_json": {},
            "report": [],
            "iteration": 0,
            "plan": [],
            "user_query": ["What are the risks in this NDA?"],
            "response": [],
            "research_json": {},
            "current_agent": "",
            "next_agent": "",
            "research_output": [],
            "document_summary": "Sample NDA between TechCorp and DataSol.",
            "state_summary": "",
            "citations": [],
            "step": 0,
            "reason": [],
            "execution": {
                "risk_analyser": False,
                "negotiation_agent": False,
                "summariser": False,
                "QnA_Agent": False,
                "report_generator": False,
                "research_agent": False,
                "clause_extraction_agent": False,
            },
        }
        ok("SharedState dict created successfully")
        info(f"Keys: {list(sample.keys())}")
        return sample
    except Exception as e:
        fail(f"SharedState failed: {e}")
        import traceback; traceback.print_exc()
        return None


# ══════════════════════════════════════════════════════════
# TEST 3 — Orchestrator alone (isolated, no graph)
# ══════════════════════════════════════════════════════════
def test_orchestrator_isolated():
    head("TEST 3 — Orchestrator (LLM call, isolated)")
    try:
        from system.orchestrator import Orchestrator
        orc = Orchestrator()
        ok("Orchestrator instantiated")

        query       = "What are the risks in this NDA and can you extract the key clauses?"
        doc_summary = "Non-Disclosure Agreement between TechCorp Inc. and DataSol Ltd., California law, 3-year confidentiality."
        state_sum   = "- clauses_json: Not started\n- risk_json: Not started"

        info("Calling activate_orchestrator()...")
        raw = orc.activate_orchestrator(
            user_query=query,
            doc_summary=doc_summary,
            state_summary=state_sum,
        )
        ok("Got response from Orchestrator LLM")
        parsed = json.loads(raw)
        ok(f"Response is valid JSON")
        info(f"Plan    : {parsed.get('plan', '?')}")
        info(f"Reason  : {parsed.get('reason', '?')[:80]}...")
        info(f"Intent  : {parsed.get('intent', '?')}")
        return parsed
    except json.JSONDecodeError as e:
        fail(f"Orchestrator returned invalid JSON: {e}")
        print("  Raw output:", raw[:300])
    except Exception as e:
        fail(f"Orchestrator call failed: {e}")
        import traceback; traceback.print_exc()
    return None


# ══════════════════════════════════════════════════════════
# TEST 4 — Risk Agent alone (isolated)
# ══════════════════════════════════════════════════════════
def test_risk_agent_isolated():
    head("TEST 4 — Risk Agent (LLM call, isolated)")
    try:
        from system.risk_agent import Risk_Agent
        agent = Risk_Agent()
        ok("Risk_Agent instantiated")

        sample_clauses = json.dumps({
            "sections": [
                {"title": "Confidentiality", "text": "All disclosed information must remain confidential for 3 years."},
                {"title": "Termination",     "text": "Either party may terminate with 30 days written notice."},
                {"title": "Liability",       "text": "Receiving party is fully liable for any breach."},
            ]
        })
        info("Calling analyze_risk()...")
        result = agent.analyze_risk(sample_clauses)
        ok("Risk analysis returned successfully")
        info(f"Risk score       : {result.risk_score}")
        info(f"Missing clauses  : {result.missing_clause_detection[:80]}")
        info(f"Conflicts        : {result.conflicts[:80]}")
        info(f"Compliance flag  : {result.compliance_flag}")
        return result
    except Exception as e:
        fail(f"Risk Agent call failed: {e}")
        import traceback; traceback.print_exc()
    return None


# ══════════════════════════════════════════════════════════
# TEST 5 — Research Agent alone (isolated)
# ══════════════════════════════════════════════════════════
def test_research_agent_isolated():
    head("TEST 5 — Research Agent (LLM + web search, isolated)")
    try:
        from system.research_agent import Research_Agent
        agent = Research_Agent()
        ok("Research_Agent instantiated")
        info("Calling run() — this performs a live web search...")
        result = agent.run(
            user_query="enforceability of NDA confidentiality clauses under California law",
            clauses_json={"sections": [{"title": "Confidentiality", "text": "3-year period"}]},
        )
        ok("Research returned successfully")
        info(f"Topic          : {result.research_topic}")
        info(f"Findings count : {len(result.findings)}")
        if result.findings:
            f = result.findings[0]
            info(f"First finding  : {f.topic} — confidence={f.confidence}")
        info(f"Warnings       : {result.warnings}")
        return result
    except Exception as e:
        fail(f"Research Agent call failed: {e}")
        import traceback; traceback.print_exc()
    return None


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"\n{B}{C}{'═'*55}")
    print("  Legal Agentic System — Workflow Test Suite")
    print(f"{'═'*55}{X}\n")

    results = {}

    # --- Structure tests (no LLM) ---
    results["graph_compiles"] = test_graph_compiles() is not None
    results["shared_state"]   = test_shared_state()   is not None

    # --- LLM tests (need OPENAI_API_KEY) ---
    print(f"\n{Y}  ── LLM tests below require OPENAI_API_KEY in .env ──{X}\n")
    results["orchestrator"]    = test_orchestrator_isolated()   is not None
    results["risk_agent"]      = test_risk_agent_isolated()     is not None
    results["research_agent"]  = test_research_agent_isolated() is not None

    # --- Summary ---
    head("RESULTS SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total  = len(results)
    for name, passed_flag in results.items():
        status = f"{G}PASS{X}" if passed_flag else f"{R}FAIL{X}"
        print(f"  [{status}]  {name}")
    print(f"\n  {B}Score: {passed}/{total}{X}\n")
