import os
import sys
import boto3
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File , BackgroundTasks
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pydantic import BaseModel
import io
from pypdf import PdfReader
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
    from document_parser import DocumentProcessor
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
document_processor = DocumentProcessor()
# --- Endpoints ---
@app.get("/")
async def root():
    return {"message": "Legal AI Platform Backend is Running"}

import io
import boto3
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from pypdf import PdfReader

app = FastAPI()

# --- Configuration (Move these to env variables in production) ---
MINIO_ENDPOINT = "http://localhost:9000"
MINIO_BUCKET = "legal-uploads"
# Initialize S3 Client once (Global)
s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id="minioadmin",     # Replace with your actual key
    aws_secret_access_key="minioadmin"  # Replace with your actual secret
)

# --- The Background Worker Function ---
def process_document_background(bucket: str, file_key: str):
    """
    Downloads file from MinIO into RAM, extracts text, and prints it.
    This runs AFTER the response is sent to the user.
    """
    print(f"🔄 [Background] Starting processing for: {file_key}")
    try:
        # 1. Fetch from MinIO (Opens the stream)
        response = s3_client.get_object(Bucket=bucket, Key=file_key)
        
        # 2. Load into RAM (The "Gulp")
        # We read the stream into a BytesIO buffer so we can use it like a file.
        file_content = io.BytesIO(response['Body'].read())
        
        # 3. Parse PDF
        reader = PdfReader(file_content)
        print(f"📄 [Background] PDF Loaded. Total Pages: {len(reader.pages)}")
        
        # 4. Extract Text from First Page
        first_page_text = reader.pages[0].extract_text()
        print(f"📝 [Background] Extracted Text Snippet:\n{first_page_text[:200]}...") # Print first 200 chars
        
        # 5. (Optional) Simulate Chunk Processing
        # We verify we have data by reading the buffer size
        file_size = file_content.getbuffer().nbytes
        print(f"📊 [Background] Verified File Size in RAM: {file_size} bytes")

        print(f"✅ [Background] Processing Complete for {file_key}")

    except Exception as e:
        print(f"❌ [Background Error] Failed to process {file_key}: {str(e)}")


# --- The Main API Endpoint ---
@app.post("/upload_file")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    1. Uploads file stream directly to MinIO.
    2. Triggers background processing.
    3. Returns immediate success.
    """
    try:
        # 1. Stream Upload to MinIO (Low RAM usage)
        s3_client.upload_fileobj(
            file.file,
            MINIO_BUCKET,
            file.filename
        )
        
        # 2. Generate the internal URL (for reference)
        file_url = f"{MINIO_ENDPOINT}/{MINIO_BUCKET}/{file.filename}"
        
        # 3. Queue the Background Task
        # This tells FastAPI: "Send the response first, then run this function."
        background_tasks.add_task(process_document_background, MINIO_BUCKET, file.filename)
        
        # 4. Return Immediate Response
        return {
            "filename": file.filename, 
            "location": file_url, 
            "message": "File uploaded successfully. Processing started in background."
        }

    except Exception as e:
        # Log the specific error for debugging
        print(f"Upload failed: {e}")
        return {"error": str(e), "message": "Failed to upload to storage"}

@app.post("/negotiate")
def negotiate(request: NegotiationRequest):
    """Generates negotiation points based on clauses and identified risks."""
    result = negotiation_agent.negotiate(request.clauses, request.risks)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)