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
from langchain_text_splitters import RecursiveCharacterTextSplitter
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BACKEND_DIR, "data.txt")

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
try:
    _chroma_client = chromadb.PersistentClient(
        path=os.path.join(BACKEND_DIR, "chroma_storage")
    )
    vector_storage = _chroma_client.get_or_create_collection("legal_documents")
except Exception as e:
    print(f"Failed to initialize vector storage: {e}")
    vector_storage = None
try:
    from orchestrator import Orchestrator
    from negotiation_agent import Negotiation_Agent
    from document_parser import DocumentProcessor
except ImportError as e:
    print(f"Failed to import local modules: {e}")
text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ".", " "],
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET_NAME", "legal-uploads")

s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)


def process_document(bucket: str, file_key: str):
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n=== Task started for: {file_key} ===\n")
    try:
        response = s3_client.get_object(Bucket=bucket, Key=file_key)
        body = response["Body"].read()

        doc = fitz.open(stream=body, filetype="pdf")
        text = "".join(page.get_text() for page in doc)
        doc.close()
        chunks = text_splitter.split_text(text)
        print("split complete")
        for i, chunk in enumerate(chunks):
            vector_storage.add(
                documents = [chunk],
                ids = [f"chunk_{i}"],
                metadatas = [{"chunk_index": i, "source": file_key}]
            )
        print(f"[ChromaDB] Stored {len(chunks)} chunks in '{file_key}'")

        with open(DATA_FILE, "a", encoding="utf-8") as f:
            f.write(text)
        return "Done"

    except Exception as e:
        err = traceback.format_exc()
        with open(DATA_FILE, "a", encoding="utf-8") as f:
            f.write(f"\nERROR: {e}\n{err}\n")
        return None


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


_orchestrator = None
_negotiation_agent = None
_document_processor = None


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
        _document_processor = DocumentProcessor()
    return _document_processor


@app.get("/")
async def root():
    return {"message": "Legal AI Platform Backend is Running"}


@app.post("/upload_file")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        s3_client.upload_fileobj(file.file, MINIO_BUCKET, file.filename)
        file_url = f"{MINIO_ENDPOINT}/{MINIO_BUCKET}/{file.filename}"
        background_tasks.add_task(process_document, MINIO_BUCKET, file.filename)
        return {
            "filename": file.filename,
            "location": file_url,
            "message": "File uploaded. Processing in background.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/negotiate")
def negotiate(request: NegotiationRequest):
    try:
        return get_negotiation_agent().negotiate(request.clauses, request.risks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Negotiation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)