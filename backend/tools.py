from langchain.tools import tool
from legal_clause_extractor import LegalClauseExtractor
from risk_assessment_agent import RiskAssessmentAgent
from negotiation_agent import NegotiationAgent
from report_generator_agent import ReportGeneratorAgent
from chaining import chain
@tool("extract legal clause",description = "get the legal clauses from the document")
def extract_legal_clause(text:str) -> str:
    LCE = LegalClauseExtractor()
    return LCE.extract(text)
@tool("assess risk",description="assess the risk from the document")
def assess_risk(text:str) -> str:
    RAA = RiskAssessmentAgent()
    return RAA.assess_risk()
@tool("negotiate",description="get the negotiation points from the document")
def negotiate(text:str)->str:
    NA = NegotiationAgent()
    return NA.get_negotiation_points()
@tool("generate report",description="generate the final report from the document")
def generate_report(text:str)->str:
    RGA = ReportGeneratorAgent()
    return RGA.generate_final_report()
@tool("get legal response",description="get the legal response from the document")
def get_legal_response(query:str)->str:
    return chain.invoke(query)
