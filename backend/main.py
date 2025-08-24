from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tools import (get_legal_response,
    extract_legal_clause,
    assess_risk,
    generate_report,
    negotiate,
)
from main_agent import main_agent
from document_parser import process_and_summarize


app = FastAPI("legal assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production restrict to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload(file:UploadFile = File(...)):
    file_bytes = await file.read()
    parsed_doc = process_and_summarize(file_bytes.name)
    return {"status":"success","message":"f{file.filename} uploaded and indexed."}

@app.post("/ask")
async def ask(question:str):
    response = main_agent.run(question)
    return {"status":"success","answer":{response}}

