from typing import TypedDict,Dict
from pydantic import BaseModel
from typing import Annotated
from orchestrator import Orchestrator
from risk_analyser import Risk_Analyser
from negotiation_agent import Negotiation_Agent
from summariser import Summariser
from QnA_Agent import QnA_Agent
from negotiation_agent import Negotiation_Agent
from report_generator import Report_Generator
from research_agent import Research_Agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import Staegraph,START,END
DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"

class SharedState(TypedDict):
    document_uploaded : bool
    file_name : str
    negotiation_json : Dict[str,any]
    risk_json : Dict[str,any]
    clauses_json : Dict[str,any]
    report : Annotated[str,add_messages]
    iteration : int
    plan : Annotated[list[str],add_messages]
    user_query : Annotated[list[str],add_messages]
    response : str
    synthesizer_in : Annotated[list[str],add_messages]
    synthesizer_out : Annotated[list[str],add_messages]
    research_json : Dict[str,any]
    current_agent : str
    next_agent : str
    research_output : Annotated[list[str],add_messages]
    document_summary : str
    state_summary : json = None
    citations : list[str] = None
    routing : str = None
graph = StateGraph()
def orchestrate(state:SharedState) -> SharedState:
    orchestrator = Orchestrator()
    state_sumarry = state["state_summary"]
    doc_summary = state["document_summary"]
    user_query = state["user_query"]
    result = orchestrator.run(user_query=user_query,state_summary=state_sumarry,document_summary=doc_summary)
    state["plan"] = result.content["steps"].strip().lower()
    return state

with PostgteGraphSaver.from_conn_string(DB_URI) as checkpointer:  
    pass




    
    