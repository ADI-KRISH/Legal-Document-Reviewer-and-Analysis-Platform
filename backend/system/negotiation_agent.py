from typing import List, Literal
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda
import os 
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


Priority = Literal["High", "Medium", "Low"]
RiskLevel = Literal["High", "Medium", "Low"]


class AmendmentItem(BaseModel):
    clause_reference: str = Field(..., description="Clause heading/reference")
    original_clause: str = Field(..., description="Exact risky clause text")
    recommended_rewrite: str = Field(..., description="Safer rewritten clause text")
    rewrite_reason: str = Field(..., description="Why this rewrite reduces risk")


class NegotiationPoint(BaseModel):
    point_id: str = Field(..., description="Unique ID like NEG-001")
    point: str = Field(..., description="Negotiation talking point")
    why_it_matters: str = Field(..., description="Justification in 1-2 lines")
    priority: Priority = Field(..., description="Priority of this negotiation point")

    related_clause_reference: str = Field(..., description="Clause heading/reference this point relates to")
    related_risk_level: RiskLevel = Field(..., description="Risk level of the related clause")

    desired_outcome: str = Field(..., description="Ideal negotiated outcome")
    fallback_position: str = Field(..., description="Acceptable fallback compromise")


class PriorityRankingItem(BaseModel):
    issue: str = Field(..., description="Issue / risk / clause reference")
    priority: Priority = Field(..., description="Priority ranking")
    priority_reason: str = Field(..., description="Why ranked this way")


class NegotiationAnalysis(BaseModel):
    amendments: List[AmendmentItem] = Field(default_factory=list)
    negotiation_points: List[NegotiationPoint] = Field(default_factory=list)
    priority_ranking: List[PriorityRankingItem] = Field(default_factory=list)



class Negotiation_Agent:
    def __init__(self):
        self.model = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0
        )

        self.parser = PydanticOutputParser(pydantic_object=NegotiationAnalysis)

        self.prompt = PromptTemplate(
            input_variables=["clauses_json", "risk_json"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
            template="""
You are a Negotiation and Clause Rewrite Agent.

TASK:
Using ONLY the clauses_json and risk_json, propose safer wording and negotiation strategy.

IMPORTANT RULES:
- Do NOT invent clauses that do not exist.
- Only rewrite clauses that are explicitly risky (based on risk_json).
- Keep rewrites legally enforceable and precise.
- Output MUST follow the schema exactly.

CLAUSES JSON:
{clauses_json}

RISK ANALYSIS JSON:
{risk_json}

{format_instructions}
"""
        )

        normalize = RunnableLambda(
            lambda x: {
                "clauses_json": x["clauses_json"] if isinstance(x["clauses_json"], str) else str(x["clauses_json"]),
                "risk_json": x["risk_json"] if isinstance(x["risk_json"], str) else str(x["risk_json"]),
            }
        )

        self.chain = normalize | self.prompt | self.model | self.parser

    def negotiate(self, clauses_json, risk_json) -> NegotiationAnalysis:
        return self.chain.invoke({
            "clauses_json": clauses_json,
            "risk_json": risk_json
        })
