from google.adk.tools import FunctionTool

from chain import create_rag_chain
from retriever import get_retriever

from vector_store import create_vector_store 


print("Connecting Agent to Clinical RAG...")


db = create_vector_store(chunks=[]) 


retriever = get_retriever(db=db) 


rag_chain = create_rag_chain(retriever)

def alzheimer_pdf_lookup(query: str) -> str:
    """
    Searches the internal 2024 Alzheimer's PDF database for 
    clinical guidelines, costs, and assessment scores.
    """
    
    response = rag_chain.invoke(query)
    
    return str(response)


rag_tool = FunctionTool(alzheimer_pdf_lookup)