"""
vector_db.py — Single source of truth for the ChromaDB client and LangChain Chroma wrapper.

Both objects point to the SAME physical database:
  backend/db/chroma_storage/

and use the SAME collection name: "Legal_Docs"
so that doc_manager (write), summariser (read), and QnA_Agent (read)
all talk to the same data.
"""

import os
import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())   # walks up directories until it finds a .env file

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # → backend/
CHROMA_PATH  = os.path.join(_BACKEND_DIR, "db", "chroma_storage")
COLLECTION_NAME = "Legal_Docs"

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
legal_collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_store = Chroma(
    client=chroma_client,
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
)

def get_doc_text(file_name:str):
    results = legal_collection.get(where={"source":file_name})
    chunks = results['documents']
    if not chunks:
        return "No chunks found for this file"
    document_text = "\n\n".join(chunks)
    return document_text
def get_content(file_name:str,query:str):
    results = legal_collection.query(query_texts=[query],n_results=5,where={'source':file_name})
    return results
    