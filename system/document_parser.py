import os
import re
import time
import logging
print("Loading document_parser dependencies...")
from datetime import datetime
from dotenv import load_dotenv
print("Loading langchain...")
from langchain_chroma import Chroma 
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, UnstructuredPowerPointLoader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool
from PIL import Image

# Database Integration
from database import SessionLocal, Contract, ProcessingStatus, init_db

# Initialize DB (creates file if not exists)
init_db()

# SURYA OCR Imports (Zero Cost)
print("Loading Surya OCR...")
try:
    from surya.ocr import run_ocr
    from surya.model.detection import segformer
    from surya.model.recognition.model import load_model, load_processor
    SURYA_AVAILABLE = True
    print("Surya OCR loaded.")
except ImportError:
    SURYA_AVAILABLE = False
    logging.warning("Surya OCR not installed. Run `pip install surya-ocr` for image support.")
except Exception as e:
    print(f"Error loading Surya OCR: {e}")
    SURYA_AVAILABLE = False

# --- Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

# We only need Google API Key (Free Tier via Gemini)
DP_API_KEY = os.getenv("DP_API_KEY") # Ensure this is in your .env
API_KEY = os.getenv("google")

if not API_KEY:
    logging.warning("Google API Key not found. Please set 'google' in .env")

embeddings  = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=API_KEY
)

CHROMA_PATH = "chroma_storage"

# Initialize Chroma
vector_store = Chroma(
    collection_name="legal_docs",
    embedding_function=embeddings,
    persist_directory=CHROMA_PATH
)

# --- Text Cleaning ---
def normalise_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'page \d+ of \d+', '', text)
    text = re.sub(r'\*\*\*.*?\*\*\*', '', text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()

# --- Surya OCR Helper ---
def perform_ocr(filepath: str) -> str:
    if not SURYA_AVAILABLE:
        return "OCR Unavailable. Please install surya-ocr."
    
    try:
        image = Image.open(filepath)
        langs = ["en"] 
        
        # Load models (this happens once per call, for better performance load globally if server has RAM)
        det_processor, det_model = segformer.load_processor(), segformer.load_model()
        rec_model, rec_processor = load_model(), load_processor()

        predictions = run_ocr([image], [langs], det_model, det_processor, rec_model, rec_processor)
        
        text = ""
        # Accessing Surya result structure
        if predictions and len(predictions) > 0:
            for line in predictions[0].text_lines:
                text += line.text + "\n"
        return text
    except Exception as e:
        logging.error(f"Surya OCR Failed: {e}")
        return ""

# --- Document Handler ---
def handle_document(filepath: str) -> list:
    extracted_at = datetime.now().isoformat()
    docs = []

    try:
        ext = filepath.lower().split('.')[-1]

        if ext == 'pdf':
            loader = PyMuPDFLoader(filepath)
            docs = loader.load()

        elif ext == 'docx':
            loader = Docx2txtLoader(filepath)
            docs = loader.load()

        elif ext == 'pptx':
            loader = UnstructuredPowerPointLoader(filepath)
            docs = loader.load()

        elif ext in ('jpg', 'jpeg', 'png'):
            logging.info(f"Processing Image {filepath} with Surya OCR...")
            text = perform_ocr(filepath)
            if not text.strip():
                raise ValueError("OCR produced no text.")
            docs = [Document(page_content=text)]

        else:
            raise ValueError(f"Unsupported file type: {ext}")

        processed_docs = []
        for doc in docs:
            cleaned = normalise_text(doc.page_content)
            metadata = {
                "file_type": ext,
                "extracted_at": extracted_at,
                "source": filepath
            }
            # Only add if content is meaningful
            if len(cleaned) > 20: 
                processed_docs.append(
                    Document(page_content=cleaned, metadata=metadata)
                )

        return processed_docs

    except Exception as e:
        logging.error(f"Error processing file '{filepath}': {e}")
        return []

# --- Chunking ---
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

# --- LLM for Summarization (Using Gemini Flash - Free Tier) ---
summarizer_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", # Use the latest flash model for speed
    google_api_key=DP_API_KEY if DP_API_KEY else API_KEY
)

def generate_summary(llm, text: str) -> str:
    prompt = f"Summarize the following legal text in 2 sentences:\n{text}"
    try:
        response = llm.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        logging.warning(f"Failed to summarize chunk: {e}")
        return ""

# --- Add Summaries to Documents ---
def add_summary_to_docs(docs: list) -> list:
    summarized_docs = []
    for idx, doc in enumerate(docs):
        # We can skip summarizing very short chunks if needed
        summary = generate_summary(summarizer_llm, doc.page_content)

        new_metadata = doc.metadata.copy()
        new_metadata["summary"] = summary
        new_metadata["enriched"] = True
        new_metadata["chunk_id"] = idx

        summarized_docs.append(
            Document(page_content=doc.page_content, metadata=new_metadata)
        )

    return summarized_docs

# --- Full Pipeline ---
def process_and_summarize(filepath: str) -> list:
    db = SessionLocal()
    contract_entry = Contract(
        filename=os.path.basename(filepath),
        upload_path=filepath,
        status=ProcessingStatus.PROCESSING
    )
    db.add(contract_entry)
    db.commit()
    db.refresh(contract_entry)

    try:
        docs = handle_document(filepath)
        if not docs:
            contract_entry.status = ProcessingStatus.FAILED
            db.commit()
            return []

        # Update page count (or chunk count really)
        contract_entry.page_count = len(docs)
        
        chunked_docs = text_splitter.split_documents(docs)
        
        # Optional: For speed/cost, maybe skip summary for huge docs unless required
        summarized_docs = add_summary_to_docs(chunked_docs)

        # Update Summary in DB to first chunk's summary as a placeholder
        if summarized_docs:
            contract_entry.summary = summarized_docs[0].metadata.get("summary", "")[:500]

        # embed only once (no duplicates)
        # Add contract_id to metadata
        for doc in summarized_docs:
            doc.metadata["contract_id"] = contract_entry.id

        vector_store.add_documents(summarized_docs)

        contract_entry.status = ProcessingStatus.COMPLETED
        db.commit()
        return summarized_docs

    except Exception as e:
        logging.error(f"Pipeline Error: {e}")
        contract_entry.status = ProcessingStatus.FAILED
        db.commit()
        return []
    finally:
        db.close()

# --- LangChain Tool Registration ---
@tool
def parse_and_summarize_tool(filepath: str) -> str:
    """Parse a document (PDF, DOCX, Image) and return a summarized text output."""
    docs = process_and_summarize(filepath)
    if not docs:
        return "Failed to process document."

    output = ""
    for i, doc in enumerate(docs):
        summary = doc.metadata.get("summary", "No summary generated.")
        output += f"\n--- Chunk {i+1} ---\nSummary:\n{summary}\n"

    return output.strip()
