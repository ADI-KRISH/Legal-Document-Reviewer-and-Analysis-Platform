from langchain_text_splitters import RecursiveCharacterTextSplitter,MarkdownHeaderTextSplitter
from chromadb import PersistentClient
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from dotenv import load_dotenv, find_dotenv
import os
import hashlib
import tempfile
import fitz as fz
import pymupdf4llm as pmp
# Portable path: system/ -> project root -> backend/db/chroma_storage
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(_PROJECT_ROOT, "backend", "db", "chroma_storage")
COLLECTION_NAME = "Legal_Docs"
load_dotenv(find_dotenv())
class Document_Processor:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vector_store = PersistentClient(path=CHROMA_PATH)
        self.collection  = self.vector_store.get_or_create_collection(name=COLLECTION_NAME)
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ".", " "],
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.headers_to_split_on = [
                ("#", "Giant_Font_Text"),   
                ("##", "Medium_Font_Text"),   
                ("###", "Tiny_Bold_Text")        
            ]
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=True,
        )
    def store_data(self, file_name: str, bucket_name: str, s3_client):
        try:
            print(f"[store_data] Fetching '{file_name}' from bucket '{bucket_name}'...")
            response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
            body = response['Body'].read()
            print(f"[store_data] Downloaded {len(body)} bytes. Converting to markdown...")
            
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(body)
                tmp_path = tmp.name

            markdown = pmp.to_markdown(tmp_path)
            markdown_docs = self.markdown_splitter.split_text(markdown)
            os.unlink(tmp_path)  

            print(f"[store_data] Markdown length: {len(markdown_docs)} chunks. Splitting...")
            joined_markdown = "\n\n".join([doc.page_content for doc in markdown_docs])
            split_markdown = self.text_splitter.split_text(joined_markdown)
            print(f"[store_data] Got {len(split_markdown)} chunks. Storing in ChromaDB...")

            file_hash = hashlib.md5(file_name.encode()).hexdigest()[:8]

            try:
                existing = self.collection.get(where={"source": file_name})
                if existing["ids"]:
                    self.collection.delete(ids=existing["ids"])
                    print(f"[store_data] Deleted {len(existing['ids'])} old chunks for '{file_name}'")
            except Exception:
                pass

            for i, chunk in enumerate(split_markdown):
                self.collection.add(
                    ids=[f"{file_hash}_chunk_{i}"],
                    documents=[chunk],
                    metadatas=[{"chunk_index": i, "source": file_name}],
                )
            print(f"[ChromaDB]  Stored '{file_name}' with {len(split_markdown)} chunks.")
        except Exception as e:
            import traceback
            print(f"[store_data]  Error: {e}")
            print(traceback.format_exc())
    def get_info(self,file_name:str,query:str):
        try :
            response = self.collection.query(
                query_texts = [query],
                n_results = 5,
                where = {"source" : file_name}
            )
            return response
        except Exception as e:
            print(f"Error getting info: {e}")
            return None
