from system.report_generator_agent import ReportGeneratorAgent
from system.clause_extraction_agent import Clause_Extraction_Agent
from typing import TypedDict,Dict
from pydantic import BaseModel
from typing import Annotated
from orchestrator import Orchestrator
from risk_analyser import Risk_Analyser
from negotiation_agent import Negotiation_Agent
from synthesizer_agent import Synthesizer_Agent
from summariser import Summariser
from QnA_Agent import QnA_Agent
from negotiation_agent import Negotiation_Agent
from report_generator import Report_Generator
from research_agent import Research_Agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import Staegraph,START,END
from langchain.prompts import AIMessage
DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"

class SharedState(TypedDict):
    document_uploaded : bool
    file_name : Annotated[list[str],add_messages]
    messages : Annotated[list[str],add_messages]
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
    step  : int = 0
    reason  : Annotated[str,add_messages]
    execution : Dict[str:bool] = {
        "risk_analyser" : False,
        "negotiation_agent" : False,
        "summariser" : False,
        "QnA_Agent" : False,
        "report_generator" : False,
        "research_agent" : False,
        "clause_extraction_agent" : False
    }


graph = StateGraph()

def orchestrate(state:SharedState) -> SharedState:
    orchestrator = Orchestrator()
    state_sumarry = state["state_summary"]
    doc_summary = state["document_summary"]
    user_query = state["user_query"]
    
    if state.get('iteration') == 0 :
        result = orchestrator.run(user_query=user_query,state_summary=state_sumarry,document_summary=doc_summary)
        state["plan"] = result.content["steps"].strip().lower()
        state["reason"] = result.content["reason"].strip().lower()    
        plan = state["plan"]
        return{
            'messages' : AIMessage(content = f"Orchestrator routing to {plan[0]} "),
            'reason' : AIMessage(content = f"Orchestrator routing to {plan[0]} because {state['reason']}"),
            'iteration' : state['iteration'] + 1,
            'current_agent' : 'Orchestrator',
            'next_agent' : plan[0],
            'synthesizer_in' : state['synthesizer_in'] + AIMessage(content = plan)
            } 

    for agent in state['plan']:
        if state['execution'][agent] == False:
            return {
                'next_agent' : agent,
                'messages' : AIMessage(content = f"Orchestrator routing to {agent}"),
                'iteration' : state['iteration'] + 1,
                'current_agent' : 'Orchestrator',
            }
    return {
        'next_agent' : 'finish',
        'messages' : AIMessage(content = "Orchestrator routing to finish"),
        'iteration' : state['iteration'] + 1,
        'current_agent' : 'Orchestrator',
    }
def QNA_Agent(state:SharedState) -> SharedState:
    qna_agent = QnA_Agent(state['file_name'])
    answer = qna_agent.get_answer(state['user_query'])
    return {'messages' : AIMessage(content = answer.answer),
            'citations' : answer.citation,
            'current_agent' : 'QnA_Agent',
            'next_agent' : 'Orchestrator',
            'iteration' : state['iteration'] + 1,
            'execution' : {**state['execution'], 'QnA_Agent' : True},
            'synthesizer_in' : state['synthesizer_in'] + [AIMessage(content = answer.answer)],
            } 


def clause_extraction_agent(state:SharedState)->SharedState:
    clause_extraction_agent = Clause_Extraction_Agent()
    results = clause_extraction_agent.extract_clauses(state['file_name'])
    return {
        'clause_json': results,
        'current_agent' : 'clause_extraction_agent',
        'next_agent' : 'Orchestrator',
        'iteration' : state['iteration'] + 1,
        'execution' : {**state['execution'], 'clause_extraction_agent' : True},
        'synthesizer_in' : state['synthesizer_in'] + AIMessage(content = results)
    }

def synthesiser(state:SharedState)->SharedState:
    synthesizer = Synthesizer_Agent()
    response = synthesizer.run(state['synthesizer_in'] , state['user_query'])
    return {
        'synthesizer_out' : state['synthesizer_out'] + AIMessage(content = response),
        'current_agent' : 'synthesiser',
        'next_agent' : 'Orchestrator',
        'iteration' : state['iteration'] + 1,
        'execution' : {**state['execution'], 'synthesiser' : True},
    }

def risk_analyser(state:SharedState)->SharedState:
    risk_analyser = Risk_Analyser()
    response = risk_analyser.analyze_risk(state['clause_json'])
    return {
        'risk_json' : response,
        'current_agent' : 'risk_analyser',
        'next_agent' : 'Orchestrator',
        'iteration' : state['iteration'] + 1,
        'execution' : {**state['execution'], 'risk_analyser' : True},
        'synthesizer_in' : state['synthesizer_in'] + AIMessage(content = response)
    }


def report_generator(state:State)->State:
    report_generator_agent = ReportGeneratorAgent()
    report = report_generator_agent.generate_report(state['file_name'])
    return {
        'next_agent' : 'Orchestrator',
        'current_agent' : 'report_generator',
        'report' : report,
        'iteration' : state['iteration'] + 1,
        'execution' : {**state['execution'], 'report_generator' : True},
            }
    pass


def routing(state:SharedState) -> SharedState:
    next_agent = state.get('next_agent','finish')
    print(next_agent)
    return {'next_agent':next_agent}
    

with PostgteGraphSaver.from_conn_string(DB_URI) as checkpointer:  
    pass




    
    