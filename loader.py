import os
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import config

def load_and_split(folder_path: str = config.PDF_FOLDER) -> list:
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}. Please add PDFs.")
        return []

    pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]

    if not pdf_files:
        print(f"No PDF files found in {folder_path}.")
        return []

    
    all_docs = []
    for filename in pdf_files:
        file_path = os.path.join(folder_path, filename)
        
        
        print(f"--- Processing: {filename} (Auto-detecting OCR) ---")
        loader = UnstructuredPDFLoader(
            file_path,
            strategy="auto", 
            languages=["eng"]
        )
        
        try:
            docs = loader.load()
           
            for doc in docs:
                doc.metadata["source_file"] = filename
            all_docs.extend(docs)
        except Exception as e:
            print(f"Error loading {filename}: {e}")

    # ── 3. CHUNKING ──────────────────────────────────────────
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE, 
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=config.CHUNK_SEPARATORS
    )
    
    chunks = splitter.split_documents(all_docs)
    print(f"✅ Total chunks created: {len(chunks)}")
    
    return chunks