from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

# Import your tools
from tools import (
    get_legal_response,
    extract_legal_clause,
    assess_risk,
    negotiate,
    generate_report
)

# Import your vector store
from document_parser import vector_store

# Load env
load_dotenv()
GOOGLE_API_KEY = os.getenv("DP_API_KEY")

# Create retriever
retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 4})

# Define helper: wrap tool so it always adds context from retriever
def with_context(tool_func):
    def wrapper(user_input: str):
        # fetch context from vector store
        docs = retriever.invoke(user_input)   # updated method (instead of deprecated get_relevant_documents)
        context = "\n\n".join([d.page_content for d in docs])
        return tool_func({"question": user_input, "context": context})
    return wrapper

# Wrap all tools
tools = [
    with_context(get_legal_response),
    with_context(extract_legal_clause),
    with_context(assess_risk),
    with_context(negotiate),
    with_context(generate_report),
]

# Main system prompt for the central agent
main_prompt = """
You are the main AI legal assistant.
You will be given an input question from a user.

You have access to the following tools:
- get_legal_response: For Q&A on uploaded legal documents
- assess_risk: For detailed clause risk/compliance analysis
- negotiate: For negotiation strategy suggestions
- extract_legal_clause: For extracting clauses from text
- generate_report: For generating final structured legal reports

Your job:
- Understand the user’s question
- Pick the right tool(s) to use
- Always provide clear, concise, professional answers
- Do NOT hallucinate if the answer is not in the document
"""

# LLM (Gemini Pro)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    google_api_key=GOOGLE_API_KEY
)

# Create the orchestrator agent
main_agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={"system_message": main_prompt}
)
