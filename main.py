import os
import config 


from loader       import load_and_split
from vector_store import create_vector_store
from retriever    import get_retriever
from chain        import create_rag_chain


EXAMPLE_QUERIES = [
    "Patient is 72 years old, MMSE score is 19. What does this indicate?",
    "What are the NIA-AA 2018 diagnostic criteria for Alzheimer's?",
    "What is the difference between MCI and early stage Alzheimer's?",
    "Patient scored 23 on MoCA test — is this normal or concerning?",
    "What biomarkers confirm an Alzheimer's diagnosis?",
    "My father forgets recent events but remembers the past clearly. What stage is this?",
]


def print_banner():
    print("\n" + "═" * 62)
    print("  🧠  Alzheimer's Clinical RAG System")
    print("  Stack: Gemini 1.5 Flash · ChromaDB · LangChain LCEL")
    print("═" * 62)

def print_examples():
    print("\n💡 Example questions:")
    for i, q in enumerate(EXAMPLE_QUERIES, 1):
        print(f"   {i}. {q}")
    print()

def print_answer(response: str):
    print("\n" + "─" * 62)
    print("📋 CLINICAL ANALYSIS")
    print("─" * 62)
    print(response)
    print("─" * 62)
    print("⚠️  Clinical support tool only. Always consult a neurologist.\n")


def setup_pipeline():
    """
    Wire all modules together and return the ready chain.
    """
    # Step 1 — Load PDFs only if DB doesn't exist yet
    db_path = config.CHROMA_DB_DIR
    if not os.path.exists(db_path) or not os.listdir(db_path):
        print("\n📚 No existing DB found — starting PDF ingestion...\n")
        chunks = load_and_split(config.PDF_FOLDER)
    else:
        print(f"\n✅ DB found at '{db_path}' — skipping PDF reload.\n")
        chunks = []

    # Step 2 — Vector store (build or load)
    db = create_vector_store(chunks)

    # Step 3 — Retriever
    retriever = get_retriever(db)

    # Step 4 — RAG chain
    chain = create_rag_chain(retriever)

    return chain


def run_loop(chain):
    print("═" * 62)
    print("✅ System ready. Type your question below.")
    print("   Commands:  'examples' → show sample queries")
    print("              'quit'     → exit")
    print("═" * 62)
    print_examples()

    while True:
        try:
            query = input("🧠 Question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Goodbye!")
            break

        if query.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break

        if query.lower() == "examples":
            print_examples()
            continue

        if not query:
            print("     Please type a question.\n")
            continue

        print("\n⏳ Searching knowledge base...\n")
        try:
            response = chain.invoke(query)
            print_answer(response)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("   Check your .env file and API key status.\n")


if __name__ == "__main__":
    print_banner()
    try:
        chain = setup_pipeline()
        run_loop(chain)
    except Exception as e:
        print(f"CRITICAL STARTUP ERROR: {e}")