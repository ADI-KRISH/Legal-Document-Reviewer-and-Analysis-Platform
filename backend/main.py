import os
import sys
import boto3
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pydantic import BaseModel

# --- System Setup & Path Configuration ---
# Fix for ChromaDB/SQLite on Windows
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass # Managed via requirements.txt checks usually, but safe to ignore if standard sqlite3 works

# Add system path for modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
system_path = os.path.join(project_root, "system")
sys.path.append(system_path)

# Load environment variables
load_dotenv(os.path.join(system_path, ".env"))

# Fix for Transformers/Keras backend conflict
os.environ["KERAS_BACKEND"] = "torch"
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

# --- Import Local Modules ---
print("Starting imports...")
try:
    from document_parser import process_and_summarize
    print("✅ Imported document_parser successfully.")
except Exception as e:
    print(f"❌ Error importing document_parser: {e}")
    raise e

from orchestrator import Orchestrator
from negotiation_agent import Negotiation_Agent

print("✅ Imported Agents successfully.")

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure bucket exists
    try:
        s3_client.head_bucket(Bucket=MINIO_BUCKET)
        print(f"✅ Bucket '{MINIO_BUCKET}' exists.")
    except ClientError:
        try:
            s3_client.create_bucket(Bucket=MINIO_BUCKET)
            print(f"✅ Created bucket '{MINIO_BUCKET}'.")
        except Exception as e:
            print(f"❌ Failed to create bucket: {e}")
    yield
    # Shutdown logic if needed

# --- FastAPI App ---
app = FastAPI(lifespan=lifespan, title="Legal Document Reviewer AI")

# --- Models ---
class NegotiationRequest(BaseModel):
    clauses: dict
    risks: dict

# --- Agents Initialization ---
orchestrator = Orchestrator()
negotiation_agent = Negotiation_Agent()

# --- Endpoints ---
@app.get("/")
async def root():
    return {"message": "Legal AI Platform Backend is Running"}

@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    """Uploads a file to MinIO storage."""
    try:
        s3_client.upload_fileobj(
            file.file,
            MINIO_BUCKET,
            file.filename
        )
        file_url = f"{MINIO_ENDPOINT}/{MINIO_BUCKET}/{file.filename}"
        
        # Future: Trigger async processing here
        # process_and_summarize(file_url) 
        
        return {
            "filename": file.filename, 
            "location": file_url, 
            "message": "File streamed to MinIO storage successfully"
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to upload to storage"}

@app.post("/negotiate")
def negotiate(request: NegotiationRequest):
    """Generates negotiation points based on clauses and identified risks."""
    result = negotiation_agent.negotiate(request.clauses, request.risks)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)