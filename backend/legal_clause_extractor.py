from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("DP_API_KEY")

class LegalClauseExtractor:
  def __init__(self) -> None:
    self.llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    api_key=GOOGLE_API_KEY
    )
    
    self.prompt = PromptTemplate(
      input_variables=["text"],
    template="""
You are an expert legal contract analyst specialised in extracting structured knowledge from lengthy documents. 
You receive raw, unstructured, and possibly fragmented text from the Document Parser Agent. 
Your job is to clean, organize, and summarize the content in a way that is precise, structured, and ready for further automated analysis.

INPUT TEXT:
{text}

TASKS:

1. **Content Cleaning & Reconstruction**
   - Merge fragmented sentences from parsing.
   - Remove headers, footers, or page numbers unless they contain legal relevance.
   - Preserve original legal meaning while making the text more readable.

2. **Section Identification**
   - Detect major sections, clauses, and subclauses.
   - Assign clear, human-readable headings to each section.

3. **Summarization**
   - For each section, provide a brief summary (2–4 sentences).
   - Also generate a global summary of the entire document in under 200 words.

4. **Key Information Extraction**
   - Parties involved
   - Dates & durations
   - Obligations
   - Penalties/liabilities
   - Financial terms
   - Any special clauses (termination, arbitration, confidentiality)

OUTPUT FORMAT:
Return a JSON object with the following keys:
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

GUIDELINES:
- Preserve legal nuance — do not rephrase clauses in a way that changes meaning.
- If certain details are missing, return an empty array or null for that field.
- Do not hallucinate or infer information that is not explicitly in the text.
"""
)
    self.chain = self.prompt | self.llm
  def extract(self, text: str):
        return self.chain.invoke({"text": text}).content

