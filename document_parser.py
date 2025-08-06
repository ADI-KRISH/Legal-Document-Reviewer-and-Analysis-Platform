from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, Pptx2txtLoader
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from langchain_core.documents import Document
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
import time 
from dotenv import load_dotenv
load_dotenv()
KEY = os.getenv("DP_API_KEY")
AZURE_OCR_KEY = os.getenv("AZURE_OCR_KEY")
AZURE_OCR_ENDPOINT = os.getenv("AZURE_OCR_ENDPOINT")

def handle_pdf(filepath):
    loader = PyMuPDFLoader(filepath)
    document = loader.load()
    return document
def handle_docx(filepath):
    loader = Docx2txtLoader(filepath)
    document = loader.load()
    return document
def handle_pptx(filepath):
    loader = Pptx2txtLoader(filepath)
    document = loader.load()
    return document
cvc = ComputerVisionClient(AZURE_OCR_ENDPOINT, CognitiveServicesCredentials(AZURE_OCR_KEY))
def handle_images(filepath):
    with open(filepath,"rb")as file:
        res = cvc.read_in_stream(file,raw=True)
    operation_id = res.headers["location"].split("/")[-1]
    while True:
        result = cvc.get_read_result(operation_id)
        if result.status not in ["notStarted","running"]:
            break
        time.sleep(1)
    if result.status == "succeeded":
        text = ""
        for page in result.analyze_results.read_results:
            for line in page.lines:
                text+=line.text +"\n"
        return [Document(page_content = text,metadata={"source":filepath})]
    
def laod_doc(file_path):
    if file_path.endswith('.pdf'):
        return handle_pdf(file_path)
    elif file_path.endswith(".docx"):
        return handle_docx(file_path)
    elif file_path.endswith (".pptx"):
        return handle_pptx(file_path)
    elif file_path.endswith('jpg') or file_path.endswith('.jpeg') or file_path.endswith('.png'):
        return handle_images(file_path)
    else:
        return "unsupported file type"