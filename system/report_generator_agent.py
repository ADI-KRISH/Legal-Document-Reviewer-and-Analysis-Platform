from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import Basemodel,Field
from dotnev import load_dotenv
import os 
load_dotenv()
DB_DIR = r"C:/Users/GS Adithya Krishna/Desktop/study/agentic ai/project/backend/Database"
class ReportGeneratorOutput(BaseModel):
    Report  : str = Field(...,description="The final Report Consisting of all the intricate details of the document")
    

class ReportGeneratorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0,model="gpt-3.5-turbo")
        self.parser = PydanticOutputParser(pydantic_object=ReportGeneratorOutput)
        self.prompt = PromptTemplate(
            input_variables=["text", "source"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
            template = """ 
            You are a Report Generator Agent for a legal contract analysis system.

TASK:
Generate a comprehensive report based on the given legal text.

IMPORTANT RULES (STRICT):
- Extract ONLY information explicitly present in the input text.
- Do NOT invent clauses, parties, dates, or legal terms.
- Do NOT add external legal knowledge or assumptions.
- Preserve original contract wording inside "full_text".
- If a field is missing, return an empty list (do not guess).
- Output MUST follow the schema exactly.
- Output MUST be valid JSON only.

INPUT File Name:
- source: {source}

LEGAL TEXT:
{text}

{format_instructions}

EXTRA INSTRUCTIONS:
- clause_id must be sequential: CLS-001, CLS-002, CLS-003...
- heading should be taken from the text if present, else use a short label.
            """
        )
        def generate_report(self,text:str,source:str) -> ReportGeneratorOutput:
            self.chain = self.prompt | self.llm | self.parser
            doc_text = get_doc_text(source)
            return self.chain.invoke({"text":doc_text,"source":source})
        