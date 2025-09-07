from langchain.tools import tool
from legal_clause_extractor import LegalClauseExtractor
from risk_assessment_agent import RiskAssessmentAgent
from negotiation_agent import NegotiationAgent
from report_generator_agent import ReportGeneratorAgent
from chaining import LegalResponseAgent
# @tool("Extract input",description="Extract input details needed for the extract legal clause tool to work")
# def legal_clause_input_extractor()->str:
    
@tool("extract legal clause", description="Extract legal clauses from the uploaded document.")
def extract_legal_clause(input_data: dict) -> str:
    """input_data must include 'question' and 'context'."""
    text = input_data.get("context", "")
    LCE = LegalClauseExtractor()
    return LCE.extract(text)

@tool("assess risk", description="Assess legal risks and compliance issues from the document.")
def assess_risk(input_data: dict) -> str:
    text = input_data.get("context", "")
    RAA = RiskAssessmentAgent()
    return RAA.assess_risk(text)

@tool("negotiate", description="Suggest negotiation points and amendments from the document.")
def negotiate(input_data: dict) -> str:
    text = input_data.get("context", "")
    NA = NegotiationAgent()
    return NA.get_negotiation_points(text)

@tool("generate report", description="Generate a final structured legal analysis report.")
def generate_report(input_data: dict) -> str:
    text = input_data.get("context", "")
    RGA = ReportGeneratorAgent()
    return RGA.generate_final_report(text)

@tool(
    "get legal response",
    description="Answer ANY user question about the uploaded legal documents. "
                "Always call this if the user asks something related to the documents."
)
def get_legal_response(input_data: dict) -> str:
    question = input_data.get("question", "")
    context = input_data.get("context", "")
    LR = LegalResponseAgent()
    return LR.get_response({"question": question, "context": context})
