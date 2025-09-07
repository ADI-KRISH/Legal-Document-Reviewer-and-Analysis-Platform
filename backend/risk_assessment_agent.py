from langchain.prompts import PromptTemplate
from langchain_mistralai import ChatMistralAI
from dotenv import load_dotenv
import os

# Load API Key
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

prompt = """
You are given a JSON object containing:

**Input Structured JSON:**
{structured_input}
You are an expert legal risk and compliance analyst.
You are tasked with analyzing the provided JSON object (from the Legal Clause Extraction Agent) to extract the following:

1. **Risk Scoring**
   - Assign a risk level ("Low", "Medium", "High") for each clause or section.
   - Provide reasoning for the score.

2. **Compliance Verification**
   - Compare clauses against relevant regulations, laws, and industry standards.
   - Flag clauses that might breach compliance or lack mandatory terms.

3. **Missing Clause Detection**
   - Identify essential legal clauses that are absent (Termination, Arbitration, Confidentiality, Governing Law, Force Majeure, Limitation of Liability, Payment Terms).

4. **Conflict & Ambiguity Detection**
   - Identify clauses with contradictory terms.
   - Flag vague or ambiguous language that could be exploited.

5. **Recommendations**
   - Suggest improvements for risky clauses.
   - Recommend additions for missing clauses.
   - Provide negotiation strategies to protect the client's interest.

---

**Output JSON Schema:**
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

**Guidelines:**
- **Do NOT hallucinate** missing laws, parties, or terms — only work with provided input.
- **Preserve confidentiality** — do not store or reuse input outside this conversation.
- Be **precise and concise** in explanations.
"""

class RiskAssessmentAgent:
    def __init__(self) -> None:
        self.llm = ChatMistralAI(
            api_key=MISTRAL_API_KEY,
            model="mistral-large-latest",
            temperature=0.2
        )
        self.prompt = PromptTemplate(
            input_variables=["structured_input"],
            template=prompt
        )
        self.chain = self.prompt | self.llm

    def assess_risk(self, structured_input: str):
        response = self.chain.invoke({"structured_input": structured_input})
        return response.content if hasattr(response, "content") else response
