from langchain_huggingface import ChatHuggingFace
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

prompt_template = """
You are an expert Legal Negotiation and Amendment Drafter.

---
Context (from the legal document):
{context}

User Request / Clause Focus (optional):
{query}
---

**Your Tasks:**
1. **Amendments** – For each risky or non-compliant clause, draft a legally sound rewrite that:
   - Preserves the core meaning.
   - Reduces risk and ensures compliance.
   - Uses clear, enforceable language.
2. **Negotiation Points** – List persuasive, client-friendly talking points for negotiation.
3. **Priority Ranking** – Rank issues as High, Medium, or Low priority based on potential risk/impact to the client.

---
**Output JSON Schema:**
{
    "amendments": [
        {
            "original_clause": "Original clause text",
            "recommended_rewrite": "Rewritten clause text",
            "rewrite_reason": "Reason for the rewrite"
        }
    ],
    "negotiation_points": [
        "Point 1",
        "Point 2"
    ],
    "priority_ranking": [
        {
            "clause": "Clause text",
            "priority": "High/Medium/Low",
            "priority_reason": "Reason for priority ranking"
        }
    ]
}
---

**Guidelines:**
- Do NOT hallucinate or create clauses that are not based on the input.
- If no {query} is provided, analyze the entire {context}.
- If {query} is provided, focus only on the clause(s) related to it.
- Be concise but precise — every rewrite must be legally enforceable.
- Ensure rewrites align with common legal standards and good faith practices.
- Preserve confidentiality — never store or reuse any input outside this task.
"""

class NegotiationAgent:
    def __init__(self) -> None:
        self.llm = ChatHuggingFace(
            model="HuggingFaceH4/zephyr-7b-beta",  
            temperature=0.2
        )
        self.prompt = PromptTemplate(
            input_variables=["context", "query"],
            template=prompt_template
        )
        self.chain = self.prompt | self.llm

    def get_negotiation_points(self, context: str, query: str = "") -> str:
        """
        - If query is empty: run negotiation on the entire context.
        - If query is provided: run negotiation only for that clause/topic.
        """
        response = self.chain.invoke({"context": context, "query": query})
        return response.content
