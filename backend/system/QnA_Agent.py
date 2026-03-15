from langchain_openai import ChatOpenAI
from typing import List , Literal,Annotated
from pydantic import BaseModel,Field
from langchain_core.prompts import PromptTemplate
from  langchain_core.output_parsers import JsonOutputParser,PydanticOutputParser
from langchain_core.runnables import RunnableLambda
import os 
from dotenv import load_dotenv, find_dotenv
from chromadb import PersistentClient

load_dotenv(find_dotenv())


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CHROMA_PATH = os.path.join(_PROJECT_ROOT, "backend", "db", "chroma_storage")
class QnA_Output(BaseModel):
    answer : str = Field(...,description="Grounded answer to the question")
    citation : List[str] = Field(default_factory=list,description="chunk / page id used ")
class QnA_Agent:
    def __init__(self,file_name:str) :
        self.llm = ChatOpenAI(temperature=0,model="gpt-4o-mini")
        self.parser = PydanticOutputParser(pydantic_object=QnA_Output)
        self.prompt = PromptTemplate(input_variables=['context','query'],partial_variables= {"format_instructions" : self.parser.get_format_instructions()},template="""
                                     You are a helpful legal Agent that answers questions{query} from the given context document {context} 
                                     Rules : 
                                     -Answer the questions only based on the CONTEXT 
                                     -If the answer is not present in the CONTEXT reply with a JSON object exactly like this: {{"answer": "not found", "citation": ["not found"]}} — citation MUST always be a list of strings, never a plain string.
                                     
                                     -Do not add any assumptions or opinions or outside knowledge for now 
                                     -Keep the answer short concise and factual and professional
                                     """)
        self.file_name = file_name
        self.vector_store = PersistentClient(path=_CHROMA_PATH)
        self.collection = self.vector_store.get_or_create_collection(name="Legal_Docs")
        self.chain = self.prompt | self.llm | self.parser
    def get_answer(self, query:str) ->QnA_Output:
        print(f"[QnA_Agent] Query: {query}")
        
        document = self.collection.query(query_texts=[query],n_results=5,where={"source":self.file_name})
        chunks = document['documents'][0]      # [0] because query() returns list-of-lists
        metadatas = document['metadatas'][0]
        context_text = "\n\n".join(chunks)
        citations = []
        for d in metadatas:
            cid = d.get("chunk_index","unknown_chunk")
            src = d.get("source","unknown_source")
            citations.append(f"chunk {cid} from {src}")
        result = self.chain.invoke({"context":context_text,"query":query})
        print(result)
        if not result.citation :
            result.citation = citations
        return result
          
    