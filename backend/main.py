from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

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

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_bytes = await file.read()
    # process file content instead of .name
    parsed_doc = process_and_summarize(file_bytes)
    return {"status": "success", "message": f"{file.filename} uploaded and indexed."}

@app.post("/ask")
async def ask(question: str):
    response = main_agent.run(question)
    return {"status": "success", "answer": response}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=8000)