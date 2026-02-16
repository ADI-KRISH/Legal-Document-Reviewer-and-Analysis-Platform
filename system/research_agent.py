from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda

from duckduckgo_search import DDGS



Confidence = Literal["Low", "Medium", "High"]


class EvidenceItem(BaseModel):
    source_title: str = Field(..., description="Title of the source/article")
    source_url: str = Field(..., description="URL of the source")
    snippet: str = Field(..., description="Relevant snippet from the source")


class FindingItem(BaseModel):
    topic: str = Field(..., description="What was researched")
    summary: str = Field(..., description="Evidence-backed summary in 2-4 lines")
    confidence: Confidence = Field(..., description="Confidence based on evidence relevance")
    evidence: List[EvidenceItem] = Field(default_factory=list)


class SimilarClauseTemplate(BaseModel):
    clause_type: str = Field(..., description="e.g., Termination, Arbitration, Liability")
    clause_template: str = Field(..., description="Suggested clause template text")
    notes: str = Field(..., description="Why this wording is commonly used")


class CitationCheck(BaseModel):
    citation: str = Field(..., description="Citation to verify")
    status: Literal["Verified", "Unverified"] = Field(..., description="Verification status")
    proof_url: Optional[str] = Field(None, description="Source URL confirming citation")
    note: Optional[str] = Field(None, description="Additional note")


class ResearchOutput(BaseModel):
    research_topic: str = Field(..., description="User requested research topic")
    jurisdiction: Optional[str] = Field(None, description="Jurisdiction if detected/provided")
    findings: List[FindingItem] = Field(default_factory=list)
    similar_clauses: List[SimilarClauseTemplate] = Field(default_factory=list)
    citation_checks: List[CitationCheck] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)



def web_search(query: str, max_results: int = 5) -> List[dict]:
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "href": r.get("href", ""),
                "body": r.get("body", "")
            })
    return results


class ResearchAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

        self.parser = PydanticOutputParser(pydantic_object=ResearchOutput)

        self.prompt = PromptTemplate(
            input_variables=["user_query", "clauses_json", "search_results", "jurisdiction"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
            template="""
You are a Legal Research Agent.

You must perform evidence-first legal research.

TASK:
1) Use the search results to answer the user query.
2) Use the clauses_json only to understand contract clause type and context.
3) Provide findings with sources + confidence.
4) If evidence is weak, set confidence = Low and mention limitations.
5) Do not hallucinate court cases, sections, or citations.

USER QUERY:
{user_query}

JURISDICTION (if known):
{jurisdiction}

EXTRACTED CLAUSES JSON (for context only):
{clauses_json}

WEB SEARCH RESULTS (as raw text):
{search_results}

OUTPUT REQUIREMENTS:
- Return ONLY valid JSON according to schema.
- Evidence list must include source_title, source_url, snippet.
- If citation is not clearly verified from search results, mark Unverified.

{format_instructions}
"""
        )

        normalize = RunnableLambda(lambda x: {
            "user_query": x["user_query"],
            "clauses_json": x["clauses_json"] if isinstance(x["clauses_json"], str) else str(x["clauses_json"]),
            "search_results": x["search_results"],
            "jurisdiction": x.get("jurisdiction", None)
        })

        self.chain = normalize | self.prompt | self.llm | self.parser

    def run(self, user_query: str, clauses_json: dict | str, jurisdiction: str = None) -> ResearchOutput:
        search_queries = [
            user_query,
            f"{user_query} enforceability {jurisdiction}" if jurisdiction else f"{user_query} enforceability",
            f"{user_query} case law {jurisdiction}" if jurisdiction else f"{user_query} case law",
            f"{user_query} contract clause example"
        ]

    
        collected = []
        for q in search_queries:
            results = web_search(q, max_results=4)
            collected.extend(results)

        search_blob = ""
        for r in collected[:12]:
            search_blob += f"\nTITLE: {r['title']}\nURL: {r['href']}\nSNIPPET: {r['body']}\n"

        output = self.chain.invoke({
            "user_query": user_query,
            "clauses_json": clauses_json,
            "search_results": search_blob,
            "jurisdiction": jurisdiction
        })

        # ✅ Add warning always (legal research safety)
        if "This research is informational" not in " ".join(output.warnings):
            output.warnings.append(
                "This research is informational only and should be verified by a qualified legal professional."
            )

        return output
