from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main_agent import main_agent
from document_parser import process_and_summarize

app = FastAPI(title="legal assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production restrict to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import tempfile

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    
    parsed_doc = process_and_summarize(tmp_path)
    return {"status": "success", "message": f"{file.filename} uploaded and indexed."}


from pydantic import BaseModel

from pydantic import BaseModel

class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask(request: QuestionRequest):
    response = main_agent.run(request.question)
    return {"status":"success","answer": response}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=8000)