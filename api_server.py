"""
api_server.py
─────────────────────────────────────────────────────────────
FastAPI server for Alzheimer's Clinical RAG System
Provides API endpoints for RAG queries, authentication, and MRI analysis
─────────────────────────────────────────────────────────────
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import base64
import random
import config

from loader import load_and_split
from vector_store import create_vector_store
from retriever import get_retriever
from chain import create_rag_chain
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai

# Initialize FastAPI app
app = FastAPI(title="Alzheimer's Clinical RAG API", version="1.0.0")

# Add CORS middleware (allow frontend from Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now (will restrict in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
rag_chain = None
vision_model = None
db = None


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    response: str
    sources: list


class AnalysisRequest(BaseModel):
    age: str = None
    education: str = None
    mmse: str = None
    moca: str = None
    cdr: str = None
    gds: str = None
    symptoms: str = None
    image_data: str = None  # Base64 encoded image


class OTPRequest(BaseModel):
    email: str
    name: str
    gender: str


class OTPVerifyRequest(BaseModel):
    email: str
    otp: str


def setup_pipeline():
    """
    Wire all modules together and return the ready chain.
    Same logic as main.py but for API use.
    """
    global rag_chain, vision_model, db
    
    # Step 0 — Initialize database
    try:
        from database import Database
        db = Database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")
        print("🔄 Authentication will be disabled")
        db = None
    
    # Step 1 — Load PDFs only if DB doesn't exist yet
    try:
        db_path = config.CHROMA_DB_DIR
        if not os.path.exists(db_path) or not os.listdir(db_path):
            print("📄 Loading PDFs and creating vector store...")
            chunks = load_and_split(config.PDF_FOLDER)
            create_vector_store(chunks)
        else:
            print("✅ Vector DB already exists, skipping PDF ingestion")
        
        # Step 2 — Set up retriever
        vector_store = create_vector_store(None)
        retriever = get_retriever(vector_store)
        
        # Step 3 — Create RAG chain
        rag_chain = create_rag_chain(retriever)
        print("✅ RAG pipeline ready")
    except Exception as e:
        print(f"⚠️ RAG pipeline setup failed: {e}")
        print("🔄 Chat functionality will be disabled")
        rag_chain = None
    
    # Step 4 — Initialize Gemini Vision model
    try:
        genai.configure(api_key=config.GOOGLE_API_KEY)
        vision_model = genai.GenerativeModel('gemini-2.5-flash-lite')
        print("✅ Gemini Vision model ready")
    except Exception as e:
        print(f"⚠️ Failed to initialize Gemini Vision: {e}")
        print("🔄 Image analysis will be disabled")
        vision_model = None


@app.on_event("startup")
async def startup_event():
    """Initialize RAG pipeline on server startup"""
    print("\n" + "═" * 62)
    print("  🧠  Alzheimer's Clinical RAG API Server")
    print("  Stack: FastAPI · Gemini 2.5 Flash · ChromaDB · LangChain")
    print("═" * 62)
    setup_pipeline()
    print("═" * 62)
    print("✅ Server ready. Access the frontend at http://localhost:8000")
    print("═" * 62 + "\n")


@app.post("/api/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Process a clinical query using the RAG pipeline
    
    Args:
        request: QueryRequest with the user's question
        
    Returns:
        QueryResponse with the AI response and sources
    """
    if not rag_chain:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Invoke the RAG chain
        response = rag_chain.invoke(request.query)
        
        # Extract sources from response (they're included in the text)
        # For now, return the full response
        return QueryResponse(
            response=response,
            sources=[]  # Can be enhanced to parse sources from response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "rag_pipeline": "ready" if rag_chain else "not_initialized",
        "pdf_folder": config.PDF_FOLDER,
        "db_dir": config.CHROMA_DB_DIR
    }


@app.post("/api/analyze", response_model=QueryResponse)
async def analyze_patient(request: AnalysisRequest):
    """
    Analyze patient data with optional MRI image using Gemini Vision
    
    Args:
        request: AnalysisRequest with patient data and optional image
        
    Returns:
        QueryResponse with clinical analysis
    """
    if not rag_chain:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    # Build the query from form data
    query_parts = []
    
    if request.age:
        query_parts.append(f"Patient age: {request.age}")
    if request.mmse:
        query_parts.append(f"MMSE score: {request.mmse}")
    if request.moca:
        query_parts.append(f"MoCA score: {request.moca}")
    if request.cdr:
        query_parts.append(f"CDR score: {request.cdr}")
    if request.gds:
        query_parts.append(f"GDS stage: {request.gds}")
    if request.symptoms:
        query_parts.append(f"Symptoms: {request.symptoms}")
    
    # If image is provided, use Gemini Vision
    if request.image_data and vision_model:
        try:
            # Decode base64 image (handle padding issues)
            image_data = request.image_data
            # Remove data URL prefix if present
            if image_data.startswith('data:'):
                image_data = image_data.split(',')[1]
            # Fix base64 padding
            image_data = image_data.strip()
            missing_padding = len(image_data) % 4
            if missing_padding:
                image_data += '=' * (4 - missing_padding)
            image_bytes = base64.b64decode(image_data)
            
            # Prepare image for Gemini
            import PIL.Image
            import io
            image = PIL.Image.open(io.BytesIO(image_bytes))
            
            # Analyze with Gemini Vision
            vision_prompt = """
            Analyze this brain MRI image for signs of Alzheimer's disease or cognitive impairment.
            
            Please provide a structured analysis with:
            
            **Classification:** (Choose one: Normal, Mild Alzheimer's, Moderate Alzheimer's, Severe Alzheimer's)
            
            **Confidence:** (Provide a percentage: e.g., 75%)
            
            **Key Findings:** (Brief bullet points of abnormalities observed)
            
            **Assessment:** (2-3 sentences summary)
            
            Be concise and specific. Focus on the most relevant clinical findings.
            """
            
            vision_response = vision_model.generate_content([vision_prompt, image])
            vision_analysis = vision_response.text
            
            patient_context = '. '.join(query_parts) if query_parts else 'No additional clinical data provided'
            
            # Build response with Vision results + RAG context
            response_text = f"""
**🧠 MRI Image Analysis (Gemini Vision)**

{vision_analysis}

**Clinical Assessment**
"""
            
            # Add RAG context for clinical data
            if query_parts:
                response_text += f"""
**Clinical Data Provided:**
{patient_context}

**Clinical Guidelines (from knowledge base):**
"""
                
                # Get RAG analysis for clinical data only
                clinical_query = f"""
                Patient has the following clinical data: {patient_context}
                
                Based on NIA-AA 2018 criteria and Alzheimer's Association guidelines, please provide:
                1. What these scores indicate about cognitive status
                2. Recommended next steps
                3. Risk assessment
                """
                
                try:
                    rag_response = rag_chain.invoke(clinical_query)
                    response_text += rag_response
                except:
                    response_text += "Clinical guidelines analysis unavailable."
            else:
                response_text += """
*No clinical data provided. Add patient age, MMSE score, or symptoms for more detailed clinical assessment.*
"""
            
            response_text += """

⚠️ **Disclaimer:** This is clinical decision support only. Gemini Vision provides AI-based image analysis. Consult a licensed neurologist for diagnosis.
"""
            
            return QueryResponse(response=response_text, sources=[])
                
        except Exception as e:
            # Vision failed, fall back to text-only
            patient_context = '. '.join(query_parts) if query_parts else 'No additional clinical data provided'
            query_text = f"""
            MRI image analysis error: {str(e)}.
            
            Patient context: {patient_context}
            
            Based on clinical guidelines from the knowledge base, please provide assessment based on the clinical data provided.
            """
            
            try:
                response_text = rag_chain.invoke(query_text)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing analysis: {str(e)}")
            
            return QueryResponse(response=response_text, sources=[])
    
    else:
        # No image or no vision model - use text-only RAG
        query_text = ". ".join(query_parts) if query_parts else "Please provide patient data for analysis"
        
        try:
            if rag_chain:
                response_text = rag_chain.invoke(query_text)
            else:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model=config.GEMINI_MODEL,
                    temperature=config.GEMINI_TEMPERATURE,
                    google_api_key=config.GOOGLE_API_KEY,
                )
                response = llm.invoke(query_text)
                response_text = response.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing analysis: {str(e)}")
        
        return QueryResponse(
            response=response_text,
            sources=[]
        )


@app.post("/api/send-otp")
async def send_otp(request: OTPRequest):
    """
    Send OTP to email
    Creates/updates user and generates OTP stored in MongoDB
    """
    try:
        # Create or update user
        user = db.create_user(request.email, request.name, request.gender)
        
        # Generate OTP (this will also send email)
        otp = db.generate_otp(request.email)
        
        return JSONResponse({
            "success": True,
            "message": "OTP sent to your email",
            "otp": otp  # For demo - remove in production
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending OTP: {str(e)}")


@app.post("/api/verify-otp")
async def verify_otp(request: OTPVerifyRequest):
    """
    Verify OTP against MongoDB
    """
    try:
        is_valid = db.verify_otp(request.email, request.otp)
        
        if is_valid:
            # Get user data
            user = db.get_user(request.email)
            
            return JSONResponse({
                "success": True,
                "message": "OTP verified successfully",
                "user": {
                    "name": user["name"],
                    "gender": user["gender"],
                    "email": user["email"]
                }
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "Invalid or expired OTP"
            }, status_code=400)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying OTP: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
