import os
import sys
import io
import boto3
from io import BytesIO
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pydantic import BaseModel

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
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream

# Initialize Docling (Default settings for stability)
converter = DocumentConverter()

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
    Background task to parse the document using Docling.
    """
    print(f"🔄 [Background] Starting Docling analysis for: {file_key}")
    try:
        # 1. Fetch from MinIO
        response = s3_client.get_object(Bucket=bucket, Key=file_key)
        file_bytes = response['Body'].read()
        
        # 2. Convert using Docling Stream (Zero Disk usage)
        buf = BytesIO(file_bytes)
        doc_stream = DocumentStream(name=file_key, stream=buf)
        
        result = converter.convert(doc_stream)
        markdown_content = result.document.export_to_markdown()
        
        # 3. Log results (In production, save this to DB/Vector Store)
        print(f"✅ [Docling] Analysis Complete for {file_key}")
        print(f"📝 Markdown Snippet:\n{markdown_content[:300]}...\n")
        
        return markdown_content
    except Exception as e:
        print(f"❌ [Background Error] Failed to process document {file_key}: {e}")
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

# --- Agents Initialization ---
# Defensive init in case imports failed
try:
    orchestrator = Orchestrator()
    negotiation_agent = Negotiation_Agent()
    document_processor = DocumentProcessor()
except Exception as e:
    print(f"⚠️ Warning: Some agents failed to initialize: {e}")

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
        result = negotiation_agent.negotiate(request.clauses, request.risks)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Negotiation failed: {str(e)}")

# --- Execution ---
if __name__ == "__main__":
    import uvicorn
    # Set relative module path for reload to work if necessary
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)