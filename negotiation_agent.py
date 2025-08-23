from langchain_huggingface import ChatHuggingFace
from dotenv import load_dotenv
import os

load_dotenv()
prompt = """
You are an expert Legal Negotiation and Amendment Drafter.
You are given a structured JSON object containing:

---
{{
  "risk_analysis": [
    {{
      "clause": "Clause text...",
      "risk_level": "High",
      "reason": "Explanation of why it's high risk."
    }}
  ],
  "compliance_issues": [
    {{
      "clause": "Clause text...",
      "issue": "Description of compliance gap.",
      "regulation": "Relevant law or standard"
    }}
  ],
  "missing_clauses": [],
  "conflicts": [
    {{
      "clause_1": "First clause text...",
      "clause_2": "Second clause text...",
      "conflict": "Explanation of conflict."
    }}
  ],
  "recommendations": [
    {{
      "clause": "Clause text...",
      "suggestion": "Suggested improvement."
    }}
  ]
}}
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
{{
    "amendments": [
        {{
            "original_clause": "Original clause text",
            "recommended_rewrite": "Rewritten clause text",
            "rewrite_reason": "Reason for the rewrite"
        }}
    ],
    "negotiation_points": [
        "Point 1",
        "Point 2"
    ],
    "priority_ranking": [
        {{
            "clause": "Clause text",
            "priority": "High/Medium/Low",
            "priority_reason": "Reason for priority ranking"
        }}
    ]
}}
---

**Guidelines:**
- Do NOT hallucinate or create clauses that are not based on the input JSON.
- Be concise but precise — every rewrite must be legally enforceable.
- Ensure rewrites align with common legal standards and good faith practices.
- Preserve confidentiality — never store or reuse any input outside this task.
"""


class negotiation_agent:
    def __init__(self) -> None:
        self.llm=ChatHuggingFace(
    model="HuggingFaceH4/zephyr-7b-beta",  
    temperature=0.2)
        self.prompt = Prompt_template(template=prompt)
    def get_negotiation_points(self):
      response = self.llm.invoke(self.prompt)
      return response.content
