from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from clinical_agent.tool import rag_tool

# --- THE CLINICAL LIBRARIAN ---
# Identity: Internal Data Expert
librarian = Agent(
    name="ClinicalLibrarian",
    model=Gemini(model="gemini-2.5-flash-lite"),
   
    instruction="""You are an expert on the 2024 and 2025 Alzheimer's Association reports. 
    Use the `alzheimer_pdf_lookup` tool to find accurate statistics and clinical facts. 
    Always cite the specific Source File name and Page numbers provided by the tool. 
    If data isn't in the PDFs, state: 'Not found in internal archives.'""",
    tools=[rag_tool],
    output_key="internal_findings"
)


researcher = Agent(
    name="WebResearcher",
    model=Gemini(model="gemini-2.5-flash-lite"),
    tools=[google_search],
  
    instruction="""
    Analyze the information provided by the ClinicalLibrarian. 
    1. If the Librarian already provided a complete, definitive answer from the PDFs, DO NOT use the google_search tool. 
    2. ONLY use google_search if the information is missing, outdated (pre-2025), or requires a 2026 update.
    3. If you do a search, present it as 'Latest 2026 Updates'.
    """
)