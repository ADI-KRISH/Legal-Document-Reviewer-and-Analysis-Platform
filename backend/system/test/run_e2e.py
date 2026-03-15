"""
End-to-end test runner for the Legal Document Agentic System.

Usage (from backend/):
    python -m system.test.run_e2e

Or from backend/system/test/ with venv activated:
    python run_e2e.py
"""

import sys
import os
import json

# ── Path setup ─────────────────────────────────────────────────────────────────
# Makes "system.*" importable regardless of where you run from
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from system.state import build_graph, SharedState

# ── ANSI colours ───────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def banner(text: str):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}\n")

def section(label: str, value):
    print(f"  {YELLOW}{BOLD}{label}:{RESET} {value}")


# ── Sample document ────────────────────────────────────────────────────────────
SAMPLE_DOC_SUMMARY = """
This is a Non-Disclosure Agreement (NDA) between TechCorp Inc. (Disclosing Party)
and DataSol Ltd. (Receiving Party), signed on January 1, 2025.

Key terms:
- Confidentiality period: 3 years from the date of signing
- Governing law: State of California
- Arbitration: All disputes to be settled via binding arbitration in San Francisco
- Termination: Either party may terminate with 30 days written notice
- Liability: The Receiving Party is liable for any breach of confidentiality
- No exclusion clause for gross negligence
"""

SAMPLE_FILE_NAME = "sample_nda.txt"


# ── Test scenarios ─────────────────────────────────────────────────────────────

TESTS = [
    # {
    #     "name": "Test 1 — Research Only (no document)",
    #     "query": "What are the standard enforceability rules for NDAs under California law?",
    #     "file_name": None,
    #     "doc_summary": "",
    # },
    {
        "name": "Test 2 — Clause Extraction + Risk Analysis",
        "query": "Extract all clauses from the contract and identify the risky ones.",
        "file_name": SAMPLE_FILE_NAME,
        "doc_summary": SAMPLE_DOC_SUMMARY,
    },
    {
        "name": "Test 3 — Q&A on Document",
        "query": "What is the confidentiality period mentioned in this NDA?",
        "file_name": SAMPLE_FILE_NAME,
        "doc_summary": SAMPLE_DOC_SUMMARY,
    },
]


# ── Runner ─────────────────────────────────────────────────────────────────────

def run_test(graph, test: dict, thread_id: str):
    banner(test["name"])

    initial_state: SharedState = {
        "document_uploaded": bool(test["file_name"]),
        "file_name": [test["file_name"]] if test["file_name"] else [],
        "results": [],
        "messages": [],
        "negotiation_json": {},
        "risk_json": {},
        "clauses_json": {},
        "report": [],
        "iteration": 0,
        "plan": [],
        "user_query": [test["query"]],
        "response": [],
        "research_json": {},
        "current_agent": "",
        "next_agent": "",
        "research_output": [],
        "document_summary": test["doc_summary"],
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

    config = {"configurable": {"thread_id": thread_id}}

    print(f"  {YELLOW}Query:{RESET} {test['query']}\n")

    try:
        final_state = None
        print(f"  {CYAN}Streaming agent steps...{RESET}\n")

        for step in graph.stream(initial_state, config=config):
            for node_name, output in step.items():
                current = output.get("current_agent", node_name)
                nxt     = output.get("next_agent", "?")
                itr     = output.get("iteration", "?")
                print(f"  {GREEN}[Step {itr}]{RESET} Agent={BOLD}{current}{RESET}  →  next={BOLD}{nxt}{RESET}")
            final_state = step

        print(f"\n{GREEN}✅ Run complete!{RESET}\n")

        # Pull the last node's output
        last_output = list(final_state.values())[-1] if final_state else {}

        response_list = last_output.get("response", [])
        response_text = response_list[-1] if response_list else "(no response)"
        section("Final Response", response_text[:500])

        citations = last_output.get("citations", [])
        if citations:
            section("Citations", citations[:3])

        # if last_output.get("research_json"):
        #     section("Research Topic", last_output["research_json"].get("research_topic", "N/A"))

        if last_output.get("clauses_json"):
            section("Clauses extracted", "✅ Yes")

        if last_output.get("risk_json"):
            section("Risk score", last_output["risk_json"].get("risk_score", "N/A"))

    except Exception as e:
        print(f"\n  {RED}❌ Error during run:{RESET} {e}")
        import traceback
        traceback.print_exc()


def main():
    banner("Legal Document Agentic System — E2E Test Runner")

    print(f"  {CYAN}Building graph...{RESET}")
    try:
        graph = build_graph()
        print(f"  {GREEN}✅ Graph compiled successfully!{RESET}")
        print(f"  Nodes: {list(graph.nodes)}\n")
    except Exception as e:
        print(f"  {RED}❌ Failed to build graph: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return

    # Run each test scenario
    for i, test in enumerate(TESTS):
        run_test(graph, test, thread_id=f"test-thread-{i}")

    banner("All tests complete")


if __name__ == "__main__":
    main()
