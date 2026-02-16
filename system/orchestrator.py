from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()


class Orchestrator:
    def __init__(self):
        self.model = ChatOpenAI(
            model="gpt-4o",
            temperature=0.0
        )

        self.system_message = SystemMessage(
            content="You are an expert orchestrator that understands user inputs and creates a correct execution plan using the available agents."
        )

        self.prompt = PromptTemplate(
            input_variables=["user_query", "state_summary"],
            template="""
You are the Orchestrator (Planner Agent) for a Multi-Agent Legal Document Reviewer system.

Your task:
- Read the user query
- Look at the current shared state summary
- Decide which agents must be executed and in what order
- Return a JSON execution plan ONLY (no extra text)

------------------------------------------------------------
AVAILABLE AGENTS (TOOLS)
------------------------------------------------------------


1) QA / RAG Legal Question Answering Agent
Purpose:
- Answers factual questions about the document using vector database retrieval
- Should return grounded answer (no hallucinations)
Outputs:
- "answer": string
- "citations": list (chunk_ids or metadata references)

When to use:
- When user asks: meaning of a clause, what is written, payment amount, dates, parties, etc.


2) Clause Extraction Agent
Purpose:
- Extracts structured clauses from contract text
- Identifies sections and key entities:
  - parties, dates, obligations, payments, liabilities
  - termination, confidentiality, arbitration, governing law
Outputs (JSON):
{{
  "sections": [...],
  "key_entities": {{...}}
}}

When to use:
- When user asks: "extract clauses", "summarize clauses", "structure the contract"
- Also required as input before Risk Agent (if clauses not available in state)


3) Risk and Compliance Agent
Purpose:
- Analyzes risks from extracted clauses
- Outputs JSON containing:
  1) risk score (high/medium/low)
  2) missing clause detection
  3) conflict and ambiguity detection
  4) compliance flags (yes/no)
Outputs (JSON):
{{
  "risk_analysis": [...],
  "missing_clauses": [...],
  "conflicts": [...],
  "compliance_flags": [...]
}}

When to use:
- When user asks: "find risks", "compliance check", "what is dangerous", "issues in contract"
- Requires Clause Extraction output first if not already present


4) Negotiation Agent
Purpose:
- Suggests improvements and negotiation points using Risk Agent output
- Outputs JSON containing:
  1) rewritten clauses in safer wording
  2) negotiation points
  3) priority ranking
Outputs (JSON):
{{
  "amendments": [...],
  "negotiation_points": [...],
  "priority_ranking": [...]
}}

When to use:
- When user asks: "rewrite", "suggest edits", "negotiation strategy", "improve clause"
- Requires Risk Agent output first

6)Research Agent
Purpose:
- Conducts research on legal topics based on user query
-Find similar contract precedents 
-Identify how clauses have been interpreted in court 
-Check citation validity
-Is connected to legal databases and APIs 
When to use :
- User explicitly asks for legal research or wants to understand legal aspects
-Requires clause extraction to know what to research 


7)  Report Generator Agent
Purpose:
- Creates a professional client-ready report combining all analysis:
  - executive summary
  - key risks & compliance issues
  - amendments / negotiation points
  - priority action plan
Outputs:
- "report_markdown": string (or structured report)

When to use:
- When user asks: "generate report", "final report", "complete review", "full review summary and things like this . If you plan to call this agent then dont use synthesizer agent in that case this should be the last agent "
- Requires Clause + Risk + Negotiation outputs first

8) Synthesizer Agent 
Purpose :
- Synthesizes the output of all the agents  into a final report and is sent back to the user 
Outputs: 
- "synthesized report" : string
When to use :
- When user asks : "synthesize report"
This should be the last agent to be called as in it responsible for generating the final report unless the user is asking for a final report and you have chosen the report generator agent 

------------------------------------------------------------
STATE SUMMARY (what already exists)
------------------------------------------------------------
State summary will be given as:
{state_summary}

Examples:
- clauses_json exists or not
- risk_json exists or not
- negotiation_json exists or not
- report exists or not

RULES:
- Do not repeat steps if the output is already in the state.
- Follow correct dependency order:
  Clause Extraction → Risk → Negotiation → Report

------------------------------------------------------------
USER QUERY
------------------------------------------------------------
{user_query}

------------------------------------------------------------
YOUR OUTPUT (STRICT JSON ONLY)
------------------------------------------------------------
Return ONLY a JSON object in this exact format:

{{
  "intent": "qa | extract_clauses | risk_analysis | negotiation | report | full_pipeline | ingestion",
  "steps": [
    "agent_name_1",
    "agent_name_2"
  ],
  "reason": "1 short sentence why this plan was chosen"
}}

Valid agent_name values:
- "document_parser_agent"
- "qa_agent"
- "clause_extraction_agent"
- "risk_compliance_agent"
- "research agent"
- "negotiation_agent"
- "report_generator_agent"

IMPORTANT:
- Output MUST be valid JSON only
- No markdown, no extra explanation

"""
    # normalize = 
        )
    def activate_orchetrator(self,user_query,state_summary):
        message = [
            self.system_message,
            self.prompt.format(user_query=user_query, state_summary=state_summary)
        ]
        response  = self.model.invoke(message)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()
