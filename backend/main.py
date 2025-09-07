# main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile

from document_parser import process_and_summarize, vector_store
from main_agent import main_agent
app = FastAPI(title="legal assistant")
DOC = {}
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ UPLOAD ------------------
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    # Store doc in Chroma
    process_and_summarize(tmp_path)

    return {"status": "success", "message": f"{file.filename} uploaded and indexed."}


# ------------------ ASK ------------------
class QueryRequest(BaseModel):
    query: str | None = None
    question: str | None = None

@app.post("/ask")
async def ask(request: QueryRequest):
    user_input = request.query or request.question
    if not user_input:
        return {"error": "No query provided"}

    retriever = vector_store.as_retriever()
    docs = retriever.get_relevant_documents(user_input)
    if not docs:
        return {"answer": "No relevant information found in uploaded documents."}

    context_text = "\n\n".join([d.page_content for d in docs])
    DOC['latest_context'] = context_text
    
    response = main_agent.invoke({
        "input": request.query,
        'context': context_text,
    })

    return {
        "answer": response,
        "sources": [d.metadata.get("source", "unknown") for d in docs]
    }
