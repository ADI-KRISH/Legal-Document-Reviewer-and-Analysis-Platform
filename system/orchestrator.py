from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class Orchestrator_Output(BaseModel):
    reason : str = Field(description="Reason for choosing this plan")
    plan : list[str] = Field(description="List of agents to be executed")
    document_in_use = Field(description="The current Document in use for which the plan is being created")
    intent : str = Field(description="The intent of the user")
    response  : str = Field(description="The response to the user after all the results are synthesised")
    citations : list[str] = Field(description="The citations for the response")
    


class Orchestrator:
    def __init__(self):
        self.model = ChatOpenAI(
            model="gpt-4o",
            temperature=0.0
        )

        self.system_message = SystemMessage(
            content="You are an expert orchestrator that understands user inputs and creates a correct execution plan using the available agents."
        )
        self.parser = PydanticOutputParser(pydantic_object=Orchestrator_Output)

        self.prompt = PromptTemplate(
            input_variables=["user_query", "state_summary","document_summary","results"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
            template="""
You are the Orchestrator (Planner Agent) for a Multi-Agent Legal Document Reviewer system.

Your task:
- Read the user query
- Look at the current shared state summary
- Look at the document summary
- Decide which agents must be executed and in what order by referring the query and the doc summary
- Return a JSON with the plan of execution
- After the Execution of all the agents and you will be given the result 
 you will have to by yourself synthesise the output and give it back to the user 
- The response should be clear cut and concise and should be in a format that can be easily understood by the user 

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


------------------------------------------------------------
Document Summary
------------------------------------------------------------
{document_summary}

-what kind of document is this 
-what is the purpose of this document 
-what are the key terms of this document 

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

{format_instructions}

IMPORTANT:
- Output MUST be valid JSON only
- No markdown, no extra explanation

"""
    # normalize = 
        )
    DEFAULT_EMPTY_STATE = {
        "clauses_json": None,
        "risk_json": None,
        "negotiation_json": None,
        "report": None
    }

    def activate_orchestrator(self, user_query,doc_summary,state_summary=None):
        if state_summary is None:
            state_summary = self.DEFAULT_EMPTY_STATE
        message = [
            self.system_message,
            self.prompt.format(user_query=user_query, state_summary=state_summary,document_summary=doc_summary)
        ]
        response = self.model.invoke(message)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()
