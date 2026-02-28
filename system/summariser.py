from chromadb import PersistentClient
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import SystemMessage
import os 
from dotenv import load_dotenv
from chromadb import PersistentClient
load_dotenv()

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CHROMA_PATH = os.path.join(_PROJECT_ROOT, "backend", "db", "chroma_storage")
class Summariser :
    def __init__(self):
        self.model = ChatGroq(model="llama-3.3-70b-versatile",api_key=os.getenv("grok"))
        self.vector_store = PersistentClient(path=_CHROMA_PATH)
        print(self.vector_store)
        self.collection  = self.vector_store.get_or_create_collection(name="Legal_Docs")
        print(self.collection)
        self.prompt = PromptTemplate(
            input_variables=["document_text"],
            template="""
            You are a professional legal document summarizer.
            Your task is to summarize the following legal document  in under 200 words.
            Include the following information:
            1. The name of the document
            2. The date of the document
            3. The parties involved in the document
            4. The purpose of the document
            5. The key terms of the document
            6. Any other relevant information
            if any of the given requirements are not in the document then just give the summary 
            
            Document Text:
            {document_text}
            
            Provide a concise and accurate summary of the document.
            """
        )
        self.chain = self.prompt | self.model
    
    def summarize(self,file_name):
        results = self.collection.get(where={"source":file_name})
        chunks = results['documents']
        if not chunks:
            return "No chunks found for this file"
        document_text = "\n\n".join(chunks)
        return self.chain.invoke({"document_text":document_text})


