from typing import TypedDict,add_messages,Dict
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
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




    
    