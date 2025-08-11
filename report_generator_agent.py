from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    model="gpt-4o", 
    temperature=0.2,
    api_key=OPENAI_API_KEY
)

# Prompt template
final_report_prompt = PromptTemplate(
    input_variables=[
        "clean_text", 
        "sections", 
        "global_summary", 
        "key_entities", 
        "risk_analysis", 
        "compliance_issues", 
        "missing_clauses", 
        "conflicts", 
        "recommendations", 
        "amendments", 
        "negotiation_points", 
        "priority_ranking"
    ],
    template="""
You are a Senior Legal Consultant preparing a final client-ready report 
based on detailed contract analysis from multiple specialist agents.

### INPUT DATA:
- **Clean Text:** {clean_text}
- **Sections:** {sections}
- **Global Summary:** {global_summary}
- **Key Entities:** {key_entities}
- **Risk Analysis:** {risk_analysis}
- **Compliance Issues:** {compliance_issues}
- **Missing Clauses:** {missing_clauses}
- **Conflicts:** {conflicts}
- **Recommendations:** {recommendations}
- **Amendments:** {amendments}
- **Negotiation Points:** {negotiation_points}
- **Priority Ranking:** {priority_ranking}

---

### TASKS:
You must create a **professional, client-facing legal report** that:
1. **Executive Summary**
   - Summarizes the overall legal and business position.
   - Lists the top 3–5 risks and negotiation priorities.

2. **Key Risks & Compliance Gaps**
   - Present risk scores and reasoning.
   - List compliance concerns with relevant laws/standards.

3. **Recommended Amendments**
   - For each clause needing revision, show:
     - Original clause text
     - Recommended rewrite
     - Reason for rewrite

4. **Negotiation Strategy**
   - Highlight major negotiation points.
   - Recommend negotiation sequencing.

5. **Priority Actions**
   - Clearly show which items need urgent attention.

6. **Appendices**
   - Include full cleaned document text.
   - Include original extracted clauses for transparency.

---

### OUTPUT:
Return the report in **Markdown format** with:
- Proper headings
- Numbered sections
- Bullet points for clarity
- Professional, precise legal language

---
DO NOT invent information that was not provided.
"""
)

def generate_final_report(all_data: dict):
    prompt_filled = final_report_prompt.format(**all_data)
    response = llm.invoke(prompt_filled)
    return response.content
