from langchain.chains import retrieval_qa
from document_parser import vector_store
retriever = vector_store.as_retriever(search_type="mmr",search_kwargs={"k":4})
chain = retrieval_qa.from_chain_type(
    llm=llm,retriever=retriever,
    return_source_documents = True
)

