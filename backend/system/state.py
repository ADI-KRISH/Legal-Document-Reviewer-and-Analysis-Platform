# from system.report_generator_agent import ReportGeneratorAgent
from system.clause_extraction_agent import Clause_Extraction_Agent
from typing import TypedDict, Dict, Any
from pydantic import BaseModel
from typing import Annotated
from system.orchestrator import Orchestrator
from system.risk_agent import Risk_Agent
from system.summariser import Summariser
from system.QnA_Agent import QnA_Agent
from system.negotiation_agent import Negotiation_Agent
from system.report_generator_agent import Report_Generator_Agent
from system.research_agent import Research_Agent
# from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph,START,END
from langchain_core.messages import AIMessage,SystemMessage
from langgraph.checkpoint.memory import InMemorySaver

from langgraph.graph.message import add_messages
import json 

# DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"
checkpointer = InMemorySaver()
class SharedState(TypedDict):
    document_uploaded : bool
    file_name : Annotated[list[str],add_messages]
    results  : Annotated[list[Dict[str, Any]], add_messages]
    messages : Annotated[list[str],add_messages]
    negotiation_json : Dict[str, Any]
    risk_json : Dict[str, Any]
    clauses_json : Dict[str, Any]
    report : Annotated[str, add_messages]
    iteration : int
    plan : Annotated[list[str], add_messages]
    user_query : Annotated[list[str], add_messages]
    response : Annotated[list[str], add_messages]
    research_json : Dict[str, Any]
    current_agent : str
    next_agent : str
    research_output : Annotated[list[str],add_messages]
    document_summary : str
    state_summary : json = None
    citations : list[str] = None
    step  : int = 0
    reason  : Annotated[str,add_messages]
    execution : Dict[str, bool] = {
        "risk_analyser" : False,
        "negotiation_agent" : False,
        "summariser" : False,
        "QnA_Agent" : False,
        "report_generator" : False,
        "research_agent" : False,
        "clause_extraction_agent" : False
    }



def orchestrate(state:SharedState) -> SharedState:
    orchestrator = Orchestrator()
    state_sumarry = state.get("state_summary",{})
    doc_summary = state.get("document_summary","")
    user_query = state.get("user_query","")
    
    if state.get('iteration') == 0 or not state.get('plan'):
        result = orchestrator.run(user_query=user_query,state_summary=state_sumarry,document_summary=doc_summary)
        state["plan"] = result.content["plan"].strip().lower()
        state["reason"] = result.content["reason"].strip().lower()    
        state['document_name'] = result.content['document_in_use'].strip().lower()
        plan = state["plan"]
        return{
            'messages' : AIMessage(content = f"Orchestrator routing to {plan[0]} "),
            'reason' : AIMessage(content = f"Orchestrator routing to {plan[0]} because {state['reason']}"),
            'iteration' : state['iteration'] + 1,
            'current_agent' : 'Orchestrator',
            'next_agent' : plan[0],
            } 

    for agent in state['plan']:
        if state['execution'][agent] == False:
            return {
                'next_agent' : agent,
                'messages' : AIMessage(content = f"Orchestrator routing to {agent}"),
                'iteration' : state['iteration'] + 1,
                'current_agent' : 'Orchestrator',
            }
    final_response = orchestrator.invoke([SystemMessage(content="All the agents in the current plan have finished do synthesising and give the proper output")],user_query=user_query,state_summary=state_sumarry,document_summary=doc_summary)
    return {
        'next_agent' : 'finish',
        'messages' : AIMessage(content = "Orchestrator routing to finish"),
        'iteration' : state['iteration'] + 1,
        'current_agent' : 'Orchestrator',
        'response' : final_response.content,
        'citations' : final_response.citation,
    }
def negotiation_agent(state:SharedState) -> SharedState:
    negotiator = Negotiation_Agent()
    response = negotiator.negotiate(state['clauses_json'],state['risk_json'])
    return {
        'current_agent' : 'negotiation_agent',
        'next_agent' : 'Orchestrator',
        'iteration' : state['iteration'] + 1,
        'execution' : {**state['execution'], 'negotiation_agent' : True},
        'messages' : AIMessage(content = response.content),
        'citations' : response.citation,
    }
def qna_agent(state:SharedState) -> SharedState:
    qna = QnA_Agent(state['file_name'])
    answer = qna.get_answer(state['user_query'])
    return {'messages' : AIMessage(content = answer.answer),
            'citations' : answer.citation,
            'current_agent' : 'qna_agent',
            'next_agent' : 'Orchestrator',
            'iteration' : state['iteration'] + 1,
            'execution' : {**state['execution'], 'QnA_Agent' : True},
            } 


def clause_extraction_agent(state:SharedState)->SharedState:
    clause_extraction_agent = Clause_Extraction_Agent()
    results = clause_extraction_agent.extract_clauses(state['file_name'])
    return {
        'clause_json': AIMessage(content=results.content),
        'current_agent' : 'clause_extraction_agent',
        'next_agent' : 'Orchestrator',
        'iteration' : state['iteration'] + 1,
        'execution' : {**state['execution'], 'clause_extraction_agent' : True},
    }

# def synthesiser(state:SharedState)->SharedState:
#     synthesizer = Synthesizer_Agent()
#     response = synthesizer.run(state['synthesizer_in'] , state['user_query'])
#     return {
#         'current_agent' : 'synthesiser',
#         'next_agent' : 'Orchestrator',
#         'iteration' : state['iteration'] + 1,
#         'execution' : {**state['execution'], 'synthesiser' : True},
#     }

def risk_analyser(state:SharedState)->SharedState:
    risk_analyser = Risk_Agent()
    response = risk_analyser.analyze_risk(state['clause_json'])
    return {
        'risk_json' : response,
        'current_agent' : 'risk_analyser',
        'next_agent' : 'Orchestrator',
        'iteration' : state['iteration'] + 1,
        'execution' : {**state['execution'], 'risk_analyser' : True},
    }


def report_generator(state:SharedState)->SharedState:
    report_generator_agent = Report_Generator_Agent()
    report = report_generator_agent.generate_report(state['file_name'])
    return {
        'next_agent' : 'Orchestrator',
        'current_agent' : 'report_generator',
        'report' : report,
        'iteration' : state['iteration'] + 1,
        'execution' : {**state['execution'], 'report_generator' : True},
            }
def research_agent(state:SharedState)->SharedState:
    research_agent = Research_Agent()
    response = research_agent.run(state['user_query'],state['clauses_json'])
    return {
        'research_json' : response,
        'current_agent' : 'research_agent',
        'next_agent' : 'Orchestrator',
        'iteration' : state['iteration'] + 1,
        'execution' : {**state['execution'], 'research_agent' : True},
    }
    

def routing(state:SharedState):
    next_agent = state.get('next_agent','finish')
    print(next_agent)
    return next_agent


AGENT_NODE_MAP = {
    'clause_extraction_agent' : clause_extraction_agent,
    # 'synthesiser' : synthesiser,
    'risk_analyser' : risk_analyser,
    'report_generator' : report_generator,
    'QnA_Agent' : qna_agent,
    'negotiation_agent' : negotiation_agent,
    'research_agent' : research_agent,
}
def build_graph() -> SharedState:

    graph = StateGraph(SharedState)
    graph.add_node("Orchestrator",orchestrate)
    graph.add_node("QnA_Agent",qna_agent)
    graph.add_node("clause_extraction_agent",clause_extraction_agent)
    graph.add_node("risk_analyser",risk_analyser)
    graph.add_node("report_generator",report_generator)
    graph.add_node("negotiation_agent",negotiation_agent)
    graph.add_node("research_agent",research_agent)
    
    graph.set_entry_point('Orchestrator')

    graph.add_conditional_edges(
        "Orchestrator",
        routing , 
        {
            "QnA_Agent" : "QnA_Agent",
            "clause_extraction_agent" : "clause_extraction_agent",
            "risk_analyser" : "risk_analyser",
            "report_generator" : "report_generator",
        }
    )
    graph.add_edge('Orchestrator',END)
    for agent in AGENT_NODE_MAP:
        graph.add_edge(agent,"Orchestrator")
    workflow = graph.compile(checkpointer=checkpointer)
    return workflow


# with PostgteGraphSaver.from_conn_string(DB_URI) as checkpointer:  
#     pass




    
    