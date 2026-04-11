import asyncio
import os
from google.adk.runners import InMemoryRunner
from google.genai import types 
from clinical_agent.orchestrator import coordinator

async def run_agent_system():
    
    APP_NAME = "alzheimer_app"
    USER_ID = "navneet_user"
    SESSION_ID = "alzheimer_session_001"

   
    runner = InMemoryRunner(agent=coordinator, app_name=APP_NAME)
    
    
    await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    print("\n" + "="*60)
    print("ALZHEIMER'S HYBRID AGENTIC SYSTEM ACTIVE")
    print("   Internal RAG (2024/2025) + Google Search (2026)")
    print("="*60 + "\n")
    
    while True:
        try:
            query_text = input("Question (or 'quit' to exit): ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if query_text.lower() in ['quit', 'exit']:
            break
        if not query_text:
            continue
            
        print(f"\n Orchestrating research specialists...")
        
      
        user_message = types.Content(
            role='user', 
            parts=[types.Part(text=query_text)]
        )
        
        try:
            
            event_stream = runner.run_async(
                user_id=USER_ID, 
                session_id=SESSION_ID, 
                new_message=user_message
            )
            
            final_text = ""
            async for event in event_stream:
                # Identify the final response from the agent sequence
                if event.is_final_response() and event.content:
                    final_text = event.content.parts[0].text

            if final_text:
                print("\n" + "─" * 60)
                print(" FINAL CLINICAL ANALYSIS")
                print("─" * 60)
                print(final_text)
                print("─" * 60)
            else:
                print("\n  Agent sequence completed without a final response.")

        except Exception as e:
            print(f"\n Execution Error: {e}")

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        print(" Error: GOOGLE_API_KEY not found in environment.")
    else:
        try:
            asyncio.run(run_agent_system())
        except KeyboardInterrupt:
            pass