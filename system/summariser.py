from re import search
from langchain_grok import ChatGrok
from langchain_core.prompts import PromptTemplate
from langhchain_openai import OpenAIEmbeddings
from langchain_core.messages import SystemMessage
import os 
from dotenv import load_dotenv
from Chromadb.Client import PersistentClient
load_dotenv()
from langchain_chroma import Chroma
class Summariser :
    def __init__(self):
        self.model = ChatGrok(model="ChatGrok-4.1",api_key=os.getenv("grok"))
        self.vector_store = Chroma(persist_directory=r"backend/db/chroma_storage",embedding_function=OpenAIEmbeddings())
        self.collection  = self.vector_store.get_collection(name="Legal_docs")
        self.prompt = PromptTemplate(
            input_variables=["document_text"],
            template="""
            You are a professional legal document summarizer.
            Your task is to summarize the following legal document  in under 100 words.
            Include the following information:
            1. The name of the document
            2. The date of the document
            3. The parties involved in the document
            4. The purpose of the document
            5. The key terms of the document
            6. Any other relevant information
            
            Document Text:
            {document_text}
            
            Provide a concise and accurate summary of the document.
            """
        )
        self.chain = self.prompt | self.model
    
    def summarize(self,file_name):
        results = self.collection.get(where={"source":file_name})
        chunks = results.get("documents",[])
        if not chunks:
            return "No chunks found for this file"
        document_text = "\n\n".join(chunks)
        return self.chain.invoke({"document_text":document_text})


