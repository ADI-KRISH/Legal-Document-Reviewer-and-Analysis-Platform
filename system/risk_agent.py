
from langchain_core.prompts import PromptTemplate
from typing import Annotated
from pydantic import BaseModel,Field
# from langchain.agents import create_agent
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.runnables import RunnableLambda
import os
from dotenv import load_dotenv
from langchain_openai  import ChatOpenAI
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
class RiskAnalysis(BaseModel) :
    risk_score : float = Field(description="The risk score of the input clauses",gt=0,lt=1.0)
    missing_clause_detection : str = Field(description="The missing clauses from the inputed clasuses")
    conflicts : str = Field(description="The conflicts in the clauses")
    compliance_flag : bool = Field(description="The compliance flag for the clauses") 

class RiskAgent:
    def  __init__(self):
        self.model = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.0
        )
        self.parser = PydanticOutputParser(pydantic_object=RiskAnalysis)
        # self.parser = JsonOutputParser()
        # self.agent = create_agent(model=self.model,format=response)
        self.prompt = PromptTemplate(input_variables=['clauses_json'],
                    partial_variables = {"format_instructions":self.parser.get_format_instructions()},
                    template="""
You are a Risk and Compliance Analysis Agent.

TASK:
Analyze the contract risks using ONLY the provided extracted clause JSON.

IMPORTANT RULES:
- Use ONLY the information in the clauses_json.
- Do NOT invent clauses.
- Do NOT hallucinate legal citations.
- If something is missing/unknown, keep lists empty or fields as empty strings.
- Output must follow the schema exactly.

EXTRACTED CLAUSES JSON:
{clauses_json}

{format_instructions}
""")
        self.runnable_instance = RunnableLambda(
            lambda x: x if isinstance(x,dict) else {"clauses_json":x}
        )
        self.chain =self.runnable_instance | self.prompt | self.model | self.parser
    def analyze_risk(self,clauses_json:dict | str) -> RiskAnalysis:
        return self.chain.invoke(clauses_json)
        
        