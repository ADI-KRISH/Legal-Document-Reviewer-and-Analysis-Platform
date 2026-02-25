from sympy.core.basic import _get_postprocessors
import os
import sys
import boto3
import fitz
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pydantic import BaseModel
import chromadb
# from langchain_text_splitters import RecursiveCharacterTextSplitter
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BACKEND_DIR, "data.txt")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET_NAME", "legal-uploads")

try :
    sys.path.append(r"C:/Users/GS Adithya Krishna/Desktop/study/agentic ai/project/system")
    from doc_manager import Document_Processor  
except Exception as e :
    print("could not import doc_manager")

try :
    s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)
except  Exception as e:
    print(f"Error connecting to MinIO: {e}")

project_root = os.path.dirname(BACKEND_DIR)
system_path = os.path.join(project_root, "system")

if system_path not in sys.path:
    sys.path.append(system_path)

try:
    __import__("pysqlite3")
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass

load_dotenv(os.path.join(system_path, ".env"))
# try:
#     _chroma_client = chromadb.PersistentClient(
#         path=os.path.join(BACKEND_DIR, "chroma_storage")
#     )
#     vector_storage = _chroma_client.get_or_create_collection("legal_documents")
# except Exception as e:
#     print(f"Failed to initialize vector storage: {e}")
#     vector_storage = None
try:
    from orchestrator import Orchestrator
    from negotiation_agent import Negotiation_Agent
    # from document_parser import DocumentProcessor
except ImportError as e:
    print(f"Failed to import local modules: {e}")


# text_splitter = RecursiveCharacterTextSplitter(
#     separators=["\n\n", "\n", ".", " "],
#     chunk_size=1000,
#     chunk_overlap=200,
#     length_function=len,
# )



# def process_document(bucket: str, file_key: str):
#     with open(DATA_FILE, "a", encoding="utf-8") as f:
#         f.write(f"\n=== Task started for: {file_key} ===\n")
#     try:
#         response = s3_client.get_object(Bucket=bucket, Key=file_key)
#         body = response["Body"].read()

#         doc = fitz.open(stream=body, filetype="pdf")
#         text = "".join(page.get_text() for page in doc)
#         doc.close()
#         chunks = text_splitter.split_text(text)
#         print("split complete")
#         for i, chunk in enumerate(chunks):
#             vector_storage.add(
#                 documents = [chunk],
#                 ids = [f"chunk_{i}"],
#                 metadatas = [{"chunk_index": i, "source": file_key}]
#             )
#         print(f"[ChromaDB] Stored {len(chunks)} chunks in '{file_key}'")

#         with open(DATA_FILE, "a", encoding="utf-8") as f:
#             f.write(text)
#         return "Done"

#     except Exception as e:
#         err = traceback.format_exc()
#         with open(DATA_FILE, "a", encoding="utf-8") as f:
#             f.write(f"\nERROR: {e}\n{err}\n")
#         return None


_orchestrator = None
_negotiation_agent = None
_document_processor = None
_summariser = None

from summariser import Summariser
def get_summariser():
    global _summariser
    if _summariser is None:
        _summariser = Summariser()
    return _summariser



def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


def get_negotiation_agent():
    global _negotiation_agent
    if _negotiation_agent is None:
        _negotiation_agent = Negotiation_Agent()
    return _negotiation_agent

def get_document_processor():
    global _document_processor
    if _document_processor is None:
        _document_processor = Document_Processor()
    return _document_processor

def document_ingestion(file_name:str,bucket_name:str,s3_client):
    try:
        get_document_processor().store_data(file_name,bucket_name,s3_client)
    except Exception as e:
        print(f"Error ingesting document: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        s3_client.head_bucket(Bucket=MINIO_BUCKET)
    except ClientError:
        try:
            s3_client.create_bucket(Bucket=MINIO_BUCKET)
        except Exception as e:
            print(f"Storage initialization failed: {e}")
    yield


app = FastAPI(lifespan=lifespan, title="Legal Document Reviewer AI")


class NegotiationRequest(BaseModel):
    clauses: dict
    risks: dict


@app.get("/")
async def root():
    return {"message": "Legal AI Platform Backend is Running"}


@app.post("/upload_file")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        s3_client.upload_fileobj(file.file, MINIO_BUCKET, file.filename)
        file_url = f"{MINIO_ENDPOINT}/{MINIO_BUCKET}/{file.filename}"
        background_tasks.add_task(document_ingestion, file.filename, MINIO_BUCKET, s3_client)
        return {
            "filename": file.filename,
            "location": file_url,
            "message": "File uploaded. Processing in background.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/file_list")
def file_list():
    try:
        response = s3_client.list_objects(Bucket=MINIO_BUCKET)
        files = [content['Key'] for content in response.get('Contents',[])]
        return {"files":files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
# @app.get("/file_info/{file_name}/{query}") 
# def file_response(file_name: str, query: str):
#     try:
#         # Client may send filename/query wrapped in quotes (%22...%22), strip them
#         file_name = file_name.strip('"').strip("'")
#         query = query.strip('"').strip("'")
#         print(f"[file_info] file='{file_name}' query='{query}'")
#         return processor.get_info(file_name, query)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@app.get("/summary/{file_name}")
def summary(file_name:str):
    try:
        result = get_summariser().summarize(file_name)
        return {"summary":result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/negotiate")
def negotiate(request: NegotiationRequest):
    try:
        return get_negotiation_agent().negotiate(request.clauses, request.risks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Negotiation failed: {str(e)}")

@app.get("/plan/{file_name}/{query}")
def plan(file_name: str, query: str):
    try:
        state_summary = {}
        doc_summary = get_summariser().summarize(file_name)
        result = get_orchestrator().activate_orchestrator(query,doc_summary,state_summary)
        return {"plan": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)