from langchain_openai import ChatOpenAI
from typing import List , Literal,Annotated
from pydantic import BaseModel,Field
from langchain_core.prompts import PromptTemplate
from  langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda
import os 
from dotenv import load_dotenv
load_dotenv()
from document_parser import vector_store
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
class QnA_Output(BaseModel):
    answer : str = Field(...,description="GRounded answer to the question")
    citation : List[str] = Field(default_factory=list,description="chunk / page id used ")
class QnA_Agent:
    def __init__(self) :
        self.llm = ChatOpenAI(temperature=0,model="gpt-3.5-turbo")
        self.parser = PydanticOutputParser(pydantic_object=QnA_Output)
        self.prompt = PromptTemplate(input_variables=['context','query'],partial_variables= {"format_instructions" : self.parser.get_format_instructions()},template="""
                                     You are a helpful legal Agent that answers questions{query} from the given context document {context} 
                                     Rules : 
                                     -Answer the questions only based on the CONTEXT 
                                     -If the answer is not present in the CONTEXT reply exactly 'I could not find any answer related to that'
                                     -Do not add any assumptions or opinions or outside knowledge for now 
                                     -Keep the answer short concise and factual and professional
                                     """)
        
        self.chain = self.prompt | self.llm | self.parser
    def get_answer(self, query:str) ->QnA_Output:
        docs = vector_store.similarity_search(query,k=4)
        context_text = "\n\n".join([d.page_content for d in docs])
        citations = []
        for d in docs  :
            cid = d.metadata.get("chunk_id","unknown_chunk")
            src = d.metadata.get("source","unknown_source")
            citations.append(f"{cid} from {src}")
        result = self.chain.invoke({"context":context_text,"query":query})
        if not result.citation :
            result.citation = citations
        return result
          
    