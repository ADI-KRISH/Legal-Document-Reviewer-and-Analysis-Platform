from fastapi import FastAPI
from typing import Union
import sys
import os
from dotenv import load_dotenv

system_path = r"C:/Users/GS Adithya Krishna/Desktop\study/agentic ai/project\system"
sys.path.append(system_path)
load_dotenv(os.path.join(system_path, ".env"))

from orchestrator import Orchestrator
app = FastAPI()

@app.get("/")
async def root():
    return {"message" : "Hello world"}

@app.get("/items/{item_id}")
def read_item(item_id:int,q:Union[str,None] = None) :
    return {"item_id":item_id,"q":q}


orchestrator = Orchestrator()

# from orchestrator import Orchestrator
from negotiation_agent import Negotiation_Agent
from pydantic import BaseModel

class NegotiationRequest(BaseModel):
    clauses: dict
    risks: dict

# orchestrator = Orchestrator()
negotiation_agent = Negotiation_Agent()

@app.post("/negotiate")
def negotiate(request: NegotiationRequest):
    result = negotiation_agent.negotiate(request.clauses, request.risks)
    return result

# @app.post("/chat/{chat_id}")
# def chat(chat_id : int, query : str) :
#     state_summary = "No prior state available."
#     execution_plan = orchestrator.activate_orchetrator(query, state_summary)
#     return {"chat_id": chat_id, "query": query, "plan": execution_plan}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)