import os
import sys
import io
import time
import boto3
from io import BytesIO
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pydantic import BaseModel
import fitz
import traceback

# Absolute path to the backend directory (safe across uvicorn reload workers)
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BACKEND_DIR, 'data.txt')

# --- System Path Configuration ---
# Ensure the 'system' directory is in the path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
system_path = os.path.join(project_root, "system")
if system_path not in sys.path:
    sys.path.append(system_path)

# --- SQLite/ChromaDB Fix for Windows ---
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

# Load environment variables early
load_dotenv(os.path.join(system_path, ".env"))

# --- Docling Imports & Setup ---

# --- Local Module Imports ---
# These are imported after sys.path and .env setup
try:
    from orchestrator import Orchestrator
    from negotiation_agent import Negotiation_Agent
    from document_parser import DocumentProcessor
    print("✅ Successfully imported local system modules.")
except ImportError as e:
    print(f"❌ Failed to import local modules: {e}")
    # We continue so the app doesn't crash immediately, but endpoints might fail.

# --- Configuration ---
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET_NAME", "legal-uploads")

# --- S3/MinIO Client Setup ---
s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY
)

# --- Background Processing Function ---
def process_document(bucket: str, file_key: str):
    """
    Background task: fetch from MinIO and extract text using PyMuPDF.
    """
    print(f"\n🔄 [Background] Task fired for: {file_key}")

    # ✅ Marker write — confirms the task is running at all
    with open(DATA_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n=== Task started for: {file_key} ===\n")

    try:
        # Step 1: Fetch from MinIO
        print(f"  [Step 1] Fetching from MinIO...")
        response = s3_client.get_object(Bucket=bucket, Key=file_key)
        body = response['Body'].read()
        print(f"  [Step 1] ✅ Got {len(body):,} bytes")

        # Step 2: Open with PyMuPDF
        print(f"  [Step 2] Opening PDF...")
        doc = fitz.open(stream=body, filetype='pdf')
        print(f"  [Step 2] ✅ {doc.page_count} pages")

        # Step 3: Extract text
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        print(f"  [Step 3] ✅ Extracted {len(text):,} chars")

        # Write to absolute path
        with open(DATA_FILE, 'a', encoding='utf-8') as f:
            f.write(text)
        print(f"  ✅ Written to: {DATA_FILE}")
        return 'Done'

    except Exception as e:
        err = traceback.format_exc()
        print(f"❌ [Background Error] {e}\n{err}")
        with open(DATA_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\nERROR: {e}\n{err}\n")
        return None

# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure MinIO bucket exists at startup
    try:
        s3_client.head_bucket(Bucket=MINIO_BUCKET)
        print(f"✅ Bucket '{MINIO_BUCKET}' verified.")
    except ClientError:
        try:
            s3_client.create_bucket(Bucket=MINIO_BUCKET)
            print(f"✅ Created bucket '{MINIO_BUCKET}'.")
        except Exception as e:
            print(f"❌ Storage initialization failed: {e}")
    yield

# --- FastAPI App ---
app = FastAPI(lifespan=lifespan, title="Legal Document Reviewer AI")

# --- Models ---
class NegotiationRequest(BaseModel):
    clauses: dict
    risks: dict

# --- Agents: Lazy Initialization ---
# Agents are loaded on first use, NOT at startup, to avoid blocking the server.
_orchestrator = None
_negotiation_agent = None
_document_processor = None

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        print("⏳ Loading Orchestrator...")
        _orchestrator = Orchestrator()
        print("✅ Orchestrator ready.")
    return _orchestrator

def get_negotiation_agent():
    global _negotiation_agent
    if _negotiation_agent is None:
        print("⏳ Loading Negotiation Agent...")
        _negotiation_agent = Negotiation_Agent()
        print("✅ Negotiation Agent ready.")
    return _negotiation_agent

def get_document_processor():
    global _document_processor
    if _document_processor is None:
        print("⏳ Loading Document Processor...")
        _document_processor = DocumentProcessor()
        print("✅ Document Processor ready.")
    return _document_processor

# --- Endpoints ---
@app.get("/")
async def root():
    return {"message": "Legal AI Platform Backend is Running"}

@app.post("/upload_file")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Uploads a file to MinIO and triggers background Docling processing.
    """
    try:
        # 1. Stream upload to MinIO
        s3_client.upload_fileobj(
            file.file,
            MINIO_BUCKET,
            file.filename
        )
        
        file_url = f"{MINIO_ENDPOINT}/{MINIO_BUCKET}/{file.filename}"
        
        # 2. Queue background parsing
        background_tasks.add_task(process_document, MINIO_BUCKET, file.filename)
        
        return {
            "filename": file.filename,
            "location": file_url,
            "message": "File uploaded successfully. Docling is processing in the background."
        }
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/negotiate")
def negotiate(request: NegotiationRequest):
    """Generates negotiation points based on clauses and identified risks."""
    try:
        result = get_negotiation_agent().negotiate(request.clauses, request.risks)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Negotiation failed: {str(e)}")

# --- Execution ---
if __name__ == "__main__":
    import uvicorn
    # Set relative module path for reload to work if necessary
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)