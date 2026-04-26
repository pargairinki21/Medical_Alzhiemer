"""
config.py
─────────────────────────────────────────────────────────────
Single source of truth for ALL settings in the project.

Every other file imports from here — nothing is hardcoded
anywhere else. To change any behaviour, you only ever edit
THIS file.

Sections:
  1. API Keys
  2. Paths
  3. PDF / Chunking settings
  4. Embedding settings
  5. ChromaDB settings
  6. Retriever settings
  7. Gemini LLM settings
─────────────────────────────────────────────────────────────
"""

import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()


GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
MONGO_DB_URL: str = os.getenv("MONGO_DB_URL")

# Email settings (Gmail)
EMAIL_ADDRESS: str = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD")


PDF_FOLDER: str = "alzheimer_pdfs"


CHROMA_DB_DIR: str = "alzheimer_db"


CHROMA_COLLECTION: str = "alzheimer_knowledge"



CHUNK_SIZE: int = 1000


CHUNK_OVERLAP: int = 150


CHUNK_SEPARATORS: list = ["\n\n", "\n", ". ", " ", ""]



EMBEDDING_MODEL: str = "models/gemini-embedding-001"



RETRIEVER_TOP_K: int = 5


RETRIEVER_FETCH_K: int = 20


RETRIEVER_LAMBDA: float = 0.7



GEMINI_MODEL: str = "gemini-2.5-flash"


GEMINI_TEMPERATURE: float = 0.2


GEMINI_MAX_TOKENS: int = 2048