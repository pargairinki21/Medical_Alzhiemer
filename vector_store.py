"""
vector_store.py
─────────────────────────────────────────────────────────────
Responsibility: ONE job only.
  → Take text chunks from loader.py
  → Convert them to vectors using Google's embedding model
  → Save those vectors to ChromaDB on disk (first run)
  → OR load the existing ChromaDB from disk (subsequent runs)

Why separate from retriever.py?
  - vector_store.py  = STORAGE  (writing/reading the DB)
  - retriever.py     = QUERYING (searching the DB)
  These are two different concerns. Keeping them separate means
  you can swap ChromaDB for Pinecone by only editing this file.
─────────────────────────────────────────────────────────────
"""

import os
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

import config


def _get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """
    Private helper — build the Google embedding model instance.
    Called internally; not exported.
    Using a helper here means if you ever swap the embedding model,
    you change it in ONE place (config.EMBEDDING_MODEL).
    """
    return GoogleGenerativeAIEmbeddings(
        model   = config.EMBEDDING_MODEL,
        google_api_key = config.GOOGLE_API_KEY,
    )


def create_vector_store(chunks: list) -> Chroma:
    """
    Smart loader — decides whether to build or load:

    CASE 1 — DB folder exists and has files:
      → Load existing ChromaDB from disk.
      → Fast. No API calls. No re-embedding.

    CASE 2 — DB folder is missing or empty:
      → Embed every chunk using Google's embedding-001 model.
      → Save the resulting vector DB to disk.
      → This only happens ONCE.

    Args:
        chunks: List of Document objects from loader.py.
                Ignored if DB already exists on disk.

    Returns:
        Chroma instance ready to be passed to retriever.py.
    """
    embeddings = _get_embeddings()

    db_exists = (
        os.path.exists(config.CHROMA_DB_DIR)
        and os.listdir(config.CHROMA_DB_DIR)
    )

    if db_exists:
        # ── Load from disk ────────────────────────────────────
        print(f"✅ Loading existing vector DB from '{config.CHROMA_DB_DIR}'...")

        db = Chroma(
            persist_directory  = config.CHROMA_DB_DIR,
            embedding_function = embeddings,
            collection_name    = config.CHROMA_COLLECTION,
        )

        count = db._collection.count()
        print(f"   📦 {count} chunks loaded from DB\n")

    else:
        # ── Build from scratch ────────────────────────────────
        if not chunks:
            raise ValueError(
                "DB not found and no chunks provided.\n"
                "Make sure your PDFs are in the folder and re-run."
            )

        print(f"🔨 Building vector DB — embedding {len(chunks)} chunks...")
        print(f"   Model    : {config.EMBEDDING_MODEL}")
        print(f"   Save to  : {config.CHROMA_DB_DIR}")
        print(f"   ⏳ This runs once. Future runs load from disk instantly.\n")

        db = Chroma.from_documents(
            documents          = chunks,
            embedding          = embeddings,
            persist_directory  = config.CHROMA_DB_DIR,
            collection_name    = config.CHROMA_COLLECTION,
        )

        print(f"✅ Vector DB saved to '{config.CHROMA_DB_DIR}'\n")

    return db