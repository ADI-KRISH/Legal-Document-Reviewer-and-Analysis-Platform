from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
import sys

load_dotenv(find_dotenv())

# Portable path to backend/Database
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(_PROJECT_ROOT, "backend", "Database"))
from Database.vector_db import get_doc_text


class Report_Generator_Agent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        self.prompt = PromptTemplate(
            input_variables=["text", "source"],
            template="""
You are a Report Generator Agent for a legal contract analysis system.

TASK:
Generate a comprehensive, well-structured plain-text report based on the given legal document.
Include: parties, key dates, obligations, termination terms, IP rights, remedies, governing law.

RULES:
- Extract ONLY information explicitly present in the text.
- Do NOT invent clauses, parties, dates, or legal terms.
- Preserve exact contract wording for key clauses.
- Structure the report with clear numbered headings (no JSON, plain text only).

Document: {source}

LEGAL TEXT:
{text}

REPORT:
"""
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate_report(self, source: str) -> dict:
        print(f"[ReportAgent] Generating report for: {source}")
        doc_text = get_doc_text(source)
        if not doc_text:
            return {"report": "No document text found. Was the file uploaded and processed?", "source": source}
        print("[ReportAgent] Got doc text, invoking LLM...")
        report = self.chain.invoke({"text": doc_text, "source": source})
        return {"report": report, "source": source}
