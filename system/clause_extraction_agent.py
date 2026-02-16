import os
from dotenv import load_dotenv
from typing import List, Optional

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

class ClauseSection(BaseModel):
    clause_id: str = Field(..., description="Unique ID like CLS-001")
    heading: str = Field(..., description="Clause heading/title if available")
    full_text: str = Field(..., description="Exact clause text extracted from the contract")
    summary: str = Field(..., description="Short neutral summary (2-3 sentences)")
    source: Optional[str] = Field(None, description="Document source filepath or filename")
    chunk_ids: List[int] = Field(default_factory=list, description="List of chunk_ids used")


class KeyEntities(BaseModel):
    parties: List[str] = Field(default_factory=list, description="All parties mentioned")
    dates: List[str] = Field(default_factory=list, description="Important dates found")
    durations: List[str] = Field(default_factory=list, description="Contract term, notice periods, etc.")
    financial_terms: List[str] = Field(default_factory=list, description="Amounts, payment terms, fees, penalties")
    obligations: List[str] = Field(default_factory=list, description="Key obligations/responsibilities")
    liabilities: List[str] = Field(default_factory=list, description="Liability/indemnity items")

    termination_clauses: List[str] = Field(default_factory=list)
    confidentiality_clauses: List[str] = Field(default_factory=list)
    arbitration_clauses: List[str] = Field(default_factory=list)
    governing_law: List[str] = Field(default_factory=list)


class ClauseExtractionOutput(BaseModel):
    document_title: Optional[str] = Field(None, description="File name / contract name if available")
    sections: List[ClauseSection] = Field(default_factory=list, description="Extracted clause sections")
    key_entities: KeyEntities = Field(default_factory=KeyEntities)


class Clause_Extraction_Agent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
        self.parser = PydanticOutputParser(pydantic_object=ClauseExtractionOutput)

        self.prompt = PromptTemplate(
            input_variables=["text", "source", "chunk_ids"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
            template="""
You are a Clause Extraction Agent for a legal contract analysis system.

TASK:
Extract structured clauses/sections and key legal entities from the given legal text.

IMPORTANT RULES (STRICT):
- Extract ONLY information explicitly present in the input text.
- Do NOT invent clauses, parties, dates, or legal terms.
- Do NOT add external legal knowledge or assumptions.
- Preserve original contract wording inside "full_text".
- If a field is missing, return an empty list (do not guess).
- Output MUST follow the schema exactly.
- Output MUST be valid JSON only.

INPUT METADATA:
- source: {source}
- chunk_ids: {chunk_ids}

LEGAL TEXT:
{text}

{format_instructions}

EXTRA INSTRUCTIONS:
- clause_id must be sequential: CLS-001, CLS-002, CLS-003...
- heading should be taken from the text if present, else use a short label.
"""
        )

        normalize = RunnableLambda(lambda x: {
            "text": x["text"] if isinstance(x["text"], str) else str(x["text"]),
            "source": x.get("source", "unknown_source"),
            "chunk_ids": x.get("chunk_ids", []),
        })

        self.chain = normalize | self.prompt | self.llm | self.parser

    def extract_clauses(self, text: str, source: str = "unknown", chunk_ids: List[int] = None) -> ClauseExtractionOutput:
        if chunk_ids is None:
            chunk_ids = []
        return self.chain.invoke({"text": text, "source": source, "chunk_ids": chunk_ids})
