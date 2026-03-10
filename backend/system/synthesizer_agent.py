from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel,Field
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

class Synthesizer_Output(BaseModel):
    response : str = Field(...,description="Should return the sythesized response ")
    
    
class Synthesizer_Agent:
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo",temperature=0.0)
        self.parser = PydanticOutputParser(pydantic_object = Synthesizer_Output)
        self.prompt = PromptTemplate(input_variables=["context","query"],partial_variables = {"format_instructions": self.parser.get_format_instructions()
},template="""
You are a Synthesizer Agent.

GOAL:
Answer the USER QUERY using ONLY the provided CONTEXT.

RULES (STRICT):
- Do NOT add any external knowledge.
- Do NOT assume missing details.
- Do NOT invent citations or facts.
- If the context does not contain enough information to answer, respond exactly:
  "I could not find any answer related to that in the given context."
- Keep the response short, factual, and professional.

CONTEXT:
{context}

USER QUERY:
{query}

{format_instructions}
""")
        normalize = RunnableLambda(lambda x : {"context": x['context'] if isinstance(x['context'],str) else str(x['context']), 
                                               "query" : x['query'] if isinstance(x['query'],str) else str(x['query'])})
        self.chain = normalize | self.prompt | self.llm | self.parser
    def respond(self,context,query):
        return self.chain.invoke({"context":context,"query":query}) 
    
        
        