from langchain.chains import create_retrieval_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from document_parser import vector_store
from dotenv import load_dotenv
import os

class LegalResponseAgent:
    def __init__(self):
        # Load API key
        load_dotenv()
        GOOGLE_API_KEY = os.getenv("google")

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY
        )

        # Initialize retriever
        self.retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 4}
        )

        # Prompt template
        self.prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
            You are an AI-powered legal assistant. 
            You help users review, analyze, and summarize legal documents. 
            Always be precise, neutral, and professional. 

            Guidelines:
            - Use the provided CONTEXT to answer.
            - Don't hallucinate. If you do not know the answer, say:
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

        # Build chains
        self.qa_chain = create_stuff_documents_chain(self.llm, self.prompt)
        self.retrieval_chain = create_retrieval_chain(self.retriever, self.qa_chain)

    def get_response(self, question: str) -> str:
        """Takes a legal question and returns an answer using retrieved context"""
        result = self.retrieval_chain.invoke({"input": question})
        return result.get("answer", "No answer generated.")
