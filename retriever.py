"""
retriever.py
─────────────────────────────────────────────────────────────
Responsibility: ONE job only.
  → Take a ChromaDB instance from vector_store.py
  → Wrap it with an MMR retriever
  → Return that retriever to chain.py

Why MMR (Maximum Marginal Relevance) instead of plain similarity?
─────────────────────────────────────────────────────────────
Plain similarity search:
  Query: "MMSE score 18 meaning"
  Returns: The same paragraph about MMSE 5 times from nearby pages
  Problem: Gemini gets no new information from chunks 2-5

MMR search:
  Query: "MMSE score 18 meaning"
  Returns: MMSE explanation + staging criteria + MCI definition
           + clinical guidelines + recommended next steps
  Result:  Gemini gets DIVERSE, RICH context → much better answers

All tuning values (TOP_K, FETCH_K, LAMBDA) live in config.py.
─────────────────────────────────────────────────────────────
"""

from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever

import config


def get_retriever(db: Chroma) -> VectorStoreRetriever:
    """
    Build an MMR retriever from the ChromaDB instance.

    How MMR works internally:
      Step 1: Fetch FETCH_K=20 candidates by similarity
      Step 2: From those 20, pick TOP_K=5 that are:
              - Relevant to the query  (controlled by lambda_mult)
              - Different from each other (controlled by 1 - lambda_mult)

    Args:
        db: Chroma instance returned by vector_store.create_vector_store()

    Returns:
        A LangChain retriever ready to plug into chain.py
    """
    print(f"🔍 Setting up MMR Retriever:")
    print(f"   Top-K        : {config.RETRIEVER_TOP_K} chunks returned to Gemini")
    print(f"   Fetch-K      : {config.RETRIEVER_FETCH_K} candidates before MMR re-ranks")
    print(f"   Lambda       : {config.RETRIEVER_LAMBDA} (1.0=relevance, 0.0=diversity)\n")

    retriever = db.as_retriever(
        search_type   = "mmr",
        search_kwargs = {
            "k"           : config.RETRIEVER_TOP_K,
            "fetch_k"     : config.RETRIEVER_FETCH_K,
            "lambda_mult" : config.RETRIEVER_LAMBDA,
        },
    )

    return retriever