import os
import re
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from langchain_chroma import Chroma 
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, UnstructuredPowerPointLoader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.tools import tool

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials

# --- Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

AZURE_OCR_KEY = os.getenv("AZURE_OCR_KEY")
AZURE_OCR_ENDPOINT = os.getenv("AZURE_OCR_ENDPOINT")
GOOGLE_API_KEY = os.getenv("DP_API_KEY")
API_KEY  = os.getenv("google")
embeddings  = GoogleGenerativeAIEmbeddings(model= "models/embedding-001",google_api_key = API_KEY)
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
    text = re.sub(r'[^\x00-\x7F]+', '', text)  # remove non-ASCII
    text = re.sub(r'https?://\S+|www\.\S+', '', text)  # remove URLs
    text = re.sub(r'[^a-z0-9\s]', '', text)  # remove punctuation
    return text.strip()

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
            if not AZURE_OCR_KEY or not AZURE_OCR_ENDPOINT:
                raise ValueError("Azure OCR credentials are not set.")

            client = ComputerVisionClient(AZURE_OCR_ENDPOINT, CognitiveServicesCredentials(AZURE_OCR_KEY))
            with open(filepath, 'rb') as file:
                read_response = client.read_in_stream(file, raw=True)

            operation_location = read_response.headers.get('Operation-Location')
            if not operation_location:
                raise Exception("OCR failed to start operation")

            operation_id = operation_location.split('/')[-1]

            while True:
                result = client.get_read_result(operation_id)
                if result.status in ['succeeded', 'failed']:
                    break
                time.sleep(1)

            if result.status != "succeeded":
                raise Exception("OCR processing failed")

            text = ""
            for page in result.analyze_result.read_results:
                for line in page.lines:
                    text += line.text + "\n"

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
            processed_docs.append(Document(page_content=cleaned, metadata=metadata))

        return processed_docs

    except Exception as e:
        logging.error(f"Error processing file '{filepath}': {e}")
        return []

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# --- LLM for Summarization ---
summarizer_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY
)

def generate_summary(llm, text: str) -> str:
    prompt = f"Summarize the following legal text:\n{text}"
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
        summary = generate_summary(summarizer_llm, doc.page_content)
        new_metadata = doc.metadata.copy()
        new_metadata["summary"] = summary
        new_metadata["enriched"] = True
        summarized_docs.append(Document(page_content=doc.page_content, metadata=new_metadata))
    vector_store.add_documents(summarized_docs)
    return summarized_docs

# --- Wrapper Function (Full Pipeline) ---
def process_and_summarize(filepath: str) -> list:
    """
    Full pipeline to parse, clean, and summarize a document.
    """
    docs = handle_document(filepath)
    if not docs :
        return []
    chunked_docs = text_splitter.split_documents(docs)
    vector_store.add_documents(chunked_docs)
    
    return add_summary_to_docs(chunked_docs) if chunked_docs else []

# --- LangChain Tool Registration ---
@tool
def parse_and_summarize_tool(filepath: str) -> str:
    """
    Parses and summarizes a legal document.
    Accepts file paths for PDF, DOCX, PPTX, JPG, PNG.
    Returns chunked summaries in text format.
    """
    docs = process_and_summarize(filepath)
    if not docs:
        return "Failed to process document."

    output = ""
    for i, doc in enumerate(docs):
        summary = doc.metadata.get("summary", "No summary generated.")
        output += f"\n--- Chunk {i+1} ---\nSummary:\n{summary}\n"
    return output.strip()

