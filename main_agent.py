from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("DP_API_KEY")

# Import your specialized tool functions
from tools import (
    get_legal_response,
    extract_clauses,
    assess_risk,
    generate_negotiation_strategy,
    generate_final_report
)

# Wrap tools into a list
tools = [
    get_legal_response,
    extract_clauses,
    assess_risk,
    generate_negotiation_strategy,
    generate_final_report
]

# Main system prompt for the central agent
main_prompt = """
You are the main AI legal assistant.
You will be given an input: {input}

You can use the following tools:
- get_legal_response: For Q&A on uploaded legal documents
- assess_risk: For detailed clause risk/compliance analysis
- generate_negotiation_strategy: For negotiation strategy suggestions
- extract_clauses: For extracting clauses from text
- generate_final_report: For generating final structured legal reports

Your job:
- Understand the user’s question
- Pick the right tool(s)
- Return a precise and helpful answer

Rules:
- Do not hallucinate if the answer is not in context
- Be concise and professional
"""

# LLM (Gemini Pro)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    google_api_key=GOOGLE_API_KEY
)

# Create main orchestrator agent
main_agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={"system_message": main_prompt}
)
