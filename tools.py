from langchain.tools import tool
from legal_clause_extractor import LegalClauseExtractor
from risk_assessment_agent import RiskAssessmentAgent
from negotiation_agent import NegotiationAgent
from report_generator_agent import ReportGeneratorAgent

@tool
def extract_legal_clause(text:str) -> str:
    LCE = LegalClauseExtractor()
    return LCE.extract(text)
@tool
def assess_risk(text:str) -> str:
    RAA = RiskAssessmentAgent()
    return RAA.assess_risk()
@tool
def negotiate(text:str)->str:
    NA = NegotiationAgent()
    return NA.get_negotiation_points()
@tool 
def generate_report(text:str)->str:
    RGA = ReportGeneratorAgent()
    return RGA.generate_final_report()
