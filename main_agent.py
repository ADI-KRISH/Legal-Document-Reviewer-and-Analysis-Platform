from langchain.agents import initialize_agent,AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
load_dotenv()

from tools import get_legal_response,extract_clauses,assess_risk,generate_negotiation_strategy,generate_final_report
GOOGLE_API_KEY = os.getenv("DP_API_KEY")
tools = [
    get_legal_response,
    extract_clauses,
    assess_risk,
    generate_negotiation_strategy,
    generate_final_report
]

llm = ChatGoogleGenerativeAI(
    model = "gemini-2.5-pro",
    api_key = GOOGLE_API_KEY
)
main_agent = initialize_agent(
    tools = tools,
    llm = llm,
    agent = AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose = True
)