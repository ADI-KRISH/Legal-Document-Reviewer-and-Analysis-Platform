import os
import re
import time
import logging
print("Loading document_parser dependencies...")
from datetime import datetime
from dotenv import load_dotenv
print("Loading langchain...")
from langchain_chroma import Chroma 
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, UnstructuredPowerPointLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
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

# We only need OpenAI API Key
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    logging.warning("OpenAI API Key not found. Please set 'OPENAI_API_KEY' in .env")

BUCKET = "legal_uploads"
CHROMA_PATH = "chroma_storage"

class DocumentProcessor:
    def __init__(self):
        print("[DocumentProcessor] Initializing embeddings...")
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        print("[DocumentProcessor] Initializing ChromaDB vector store...")
        self.vector_storage = Chroma(
            collection_name="legal_docs",
            embedding_function=self.embeddings,
            persist_directory=CHROMA_PATH
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        print("[DocumentProcessor] Initializing LLM...")
        self.summarizer_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.bucket = BUCKET
        print("[DocumentProcessor] ✅ Ready.")
    def handle_document(self,filepath: str) -> list:
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
    def normalise_text(self,text: str) -> str:
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'page \d+ of \d+', '', text)
        text = re.sub(r'\*\*\*.*?\*\*\*', '', text)
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return text.strip()
    def perform_ocr(self,filepath: str) -> str:
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
    def generate_summary(self,llm, text: str) -> str:
        prompt = f"Summarize the following legal text in 2 sentences:\n{text}"
        try:
            response = llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logging.warning(f"Failed to summarize chunk: {e}")
        return ""
    def add_summary_to_docs(self,docs: list) -> list:
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
    def process_and_summarize(self,filepath: str) -> list:
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
# Initialize Chroma


# --- Text Cleaning ---


# --- Surya OCR Helper ---


# --- Document Handler ---

# --- Chunking ---




# --- Add Summaries to Documents ---


# --- Full Pipeline ---


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
