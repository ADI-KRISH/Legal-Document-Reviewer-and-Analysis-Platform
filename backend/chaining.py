from langchain.chains import create_retrieval_chain
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from document_parser import vector_store
from langchain.prompts import PromptTemplate
import os
from langchain.chains.combine_documents import create_stuff_documents_chain

from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY=os.getenv("google")
llm = ChatGoogleGenerativeAI(
    model = "gemini-2.0-flash",
    google_api_key=GOOGLE_API_KEY
)

retriever = vector_store.as_retriever(search_type="mmr",search_kwargs={"k":4})

GOOGLE_API_KEY=os.getenv("DP_API_KEY") 

prompt = PromptTemplate(
    template = """
    You are  an AI-powered legal assistant. 
You help users review, analyze, and summarize legal documents. 
Always be precise, neutral, and professional. 

Guidelines:
- Use the provided CONTEXT to answer.
- don't hallucinate if you do not know the answer tell you don't know. 
- If the context does not contain the answer, say: 

  "I could not find that information in the uploaded documents."
- Avoid speculation. Do not provide legal advice beyond what is in context.
- When listing clauses, risks, or obligations, present them clearly and concisely.

CONTEXT:
{context}

USER QUESTION:
{question}

FINAL ANSWER:
"""

)
question_answer_chain = create_stuff_documents_chain(llm, prompt)
qa_chain = create_retrieval_chain(
    retriever,
    question_answer_chain
)

chain = (
    {"context":retriever,"question":RunnablePassthrough()}
    |qa_chain
    |prompt
)
