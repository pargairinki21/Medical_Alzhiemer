"""
chain.py
─────────────────────────────────────────────────────────────
Responsibility: ONE job only.
  → Take a retriever from retriever.py
  → Define the clinical system prompt
  → Connect retriever → prompt → Gemini → output parser
  → Return the runnable chain to main.py

The LCEL chain (pipe | syntax) reads left to right:
  retrieve chunks → format → inject into prompt → Gemini → plain text

Why is the prompt so detailed?
  Without a precise prompt, Gemini might say:
    "MMSE score 18 means the person may have memory issues."
  With our clinical prompt, it says:
    "1. Score Analysis: 18/30 falls in the mild impairment range...
     2. Matching Criteria: Per NIA-AA 2018, this is consistent with...
     3. Risk: Early-stage Alzheimer's / MCI boundary...
     4. Next Steps: Neuropsychological battery, amyloid PET...
     5. Source: [alzheimer_facts_2024.pdf, Page 12]"
─────────────────────────────────────────────────────────────
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.vectorstores import VectorStoreRetriever

import config



SYSTEM_PROMPT = """
You are a clinical knowledge assistant specializing in Alzheimer's disease 
and cognitive impairment assessment.

You have access to authoritative clinical literature including:
- NIA-AA 2018 diagnostic criteria
- Alzheimer's Association Facts & Figures reports
- Cognitive assessment guidelines (MMSE, MoCA, CDR, GDS)
- Clinical research on biomarkers and staging

Your behaviour rules:
1. ALWAYS base your answer on the retrieved context below
2. ALWAYS cite which source document and page you are referencing
3. NEVER give a definitive medical diagnosis — provide clinical analysis only
4. ALWAYS end with a recommendation to consult a neurologist
5. If the context does not contain enough information, say:
   "This is outside my current knowledge base. Please consult clinical guidelines."
6. Be precise about scoring thresholds — never round or estimate scores

Clinical scales you should recognise:
- MMSE  : 30=normal, 24-30=possible MCI, 18-23=mild AD, 10-17=moderate AD, <10=severe AD
- MoCA  : 26-30=normal, 18-25=mild, 10-17=moderate, <10=severe impairment
- CDR   : 0=none, 0.5=MCI, 1=mild, 2=moderate, 3=severe
- GDS   : 1-2=normal, 3=MCI, 4=mild AD, 5=moderate, 6-7=severe

Retrieved Clinical Context:
{context}
"""



HUMAN_PROMPT = """
Analyze the following query based ONLY on the provided context:

{question}

---
IF THE QUESTION IS ABOUT A PATIENT OR SYMPTOMS:
Structure your response as:
1. Symptom / Score Analysis
2. Matching Clinical Criteria
3. Risk Assessment
4. Recommended Next Steps

IF THE QUESTION IS ABOUT FINANCIALS, COSTS, OR STATISTICS:
Provide a detailed factual breakdown using the data points, years, and figures from the context.
---

MANDATORY: 
List the "Sources Used" (Document name and Page number) at the end of every response.

⚠️ Reminder: This is a support analysis, not a medical diagnosis.
"""



def _format_docs(docs: list) -> str:
    """
    Convert a list of Document objects into a formatted string
    that gets injected into {context} in the system prompt.

    Each chunk is labelled with its source file + page number
    so Gemini can cite them in the answer.
    """
    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source_file", "Unknown source")
        page   = doc.metadata.get("page", "?")
        formatted.append(
            f"[Source {i} — {source}, Page {page}]\n{doc.page_content}"
        )
    return "\n\n" + ("─" * 40 + "\n\n").join(formatted)



def create_rag_chain(retriever: VectorStoreRetriever):
    """
    Assemble the full RAG chain using LangChain LCEL (pipe syntax).

    Pipeline:
      {question} ──→ retriever ──→ _format_docs ──→ {context}
                 ──→ RunnablePassthrough ──────────→ {question}
                 Both ──→ prompt ──→ Gemini ──→ StrOutputParser

    Args:
        retriever: MMR retriever from retriever.get_retriever()

    Returns:
        A runnable chain. Call with: chain.invoke("your question")
    """

   
    llm = ChatGoogleGenerativeAI(
        model          = config.GEMINI_MODEL,
        temperature    = config.GEMINI_TEMPERATURE,
        max_tokens     = config.GEMINI_MAX_TOKENS,
        google_api_key = config.GOOGLE_API_KEY,
    )

    # ── Prompt template ───────────────────────────────────────
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human",  HUMAN_PROMPT),
    ])

    
    chain = (
        {
            "context":  retriever | _format_docs,  
            "question": RunnablePassthrough(),      
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    print(f" RAG Chain ready:")
    print(f"   LLM         : {config.GEMINI_MODEL}")
    print(f"   Temperature : {config.GEMINI_TEMPERATURE}")
    print(f"   Max tokens  : {config.GEMINI_MAX_TOKENS}\n")

    return chain