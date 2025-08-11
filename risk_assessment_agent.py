from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# Load API Key
load_dotenv()
MISTRAL_API_KEY = os.getenv("mistral")

# LLM Setup
llm = ChatOpenAI(
    api_key=MISTRAL_API_KEY,
    model="mistral-large-latest",  # reasoning-optimized
)

# Prompt Template (do not pre-format here)
prompt = """
You are given a JSON object containing:
{{
  "clean_text": "Full cleaned and reconstructed document text",
  "sections": [
    {{
      "heading": "Section Title",
      "full_text": "Complete section text",
      "summary": "Brief summary of the section"
    }}
  ],
  "global_summary": "Concise overall summary of the document",
  "key_entities": {{
    "parties": [],
    "dates": [],
    "obligations": [],
    "penalties": [],
    "financial_terms": [],
    "special_clauses": []
  }}
}}

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

**Input Structured JSON:**
{structured_input}

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

# Define Prompt Template
risk_compliance_template = PromptTemplate(
    input_variables=["structured_input"],
    template=prompt
)
