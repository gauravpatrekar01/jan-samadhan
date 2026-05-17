import os
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError

# Load env
load_dotenv()

# Router
router = APIRouter()

# Gemini client
client = None
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    try:
        client = genai.Client(api_key=gemini_key)
    except Exception as e:
        print(f"CRITICAL: Failed to initialize Gemini client in chatbot: {e}")

MODEL = "gemini-3.1-flash-lite-preview"

# ─── Retry wrapper ───
if client is not None:
    _orig_gen = client.models.generate_content

    def _retry_gen(*args, **kwargs):
        for i in range(4):
            try:
                return _orig_gen(*args, **kwargs)
            except (ServerError, ClientError) as e:
                code = getattr(e, "code", None)
                if code in (429, 503) and i < 3:
                    wait = 5 * (i + 1)
                    print(f"Retrying after {wait}s due to {code}...")
                    time.sleep(wait)
                    continue
                raise

    client.models.generate_content = _retry_gen

# ─── Request schema ───
class AIRequest(BaseModel):
    query: str

# ─── FULL KNOWLEDGE BASE (PLAIN TEXT) ───
KNOWLEDGE_BASE = """
JanSamadhan is a public grievance management system. It connects citizens, officers, NGOs, and administrators. The system allows users to file complaints, track them, and get resolutions. It ensures transparency, accountability, and faster grievance handling.

The system works as a flow. A citizen submits a complaint. The system processes the complaint. It assigns a priority score and an SLA deadline. The complaint is assigned to an officer. The officer reviews and works on it. An NGO may request to handle the complaint. The admin approves or rejects the NGO request. Finally, the complaint is resolved and closed.

There are four main roles. Citizen can register, login, submit complaints, upload media, and track status. Officer can view assigned complaints, update status, and resolve them within SLA. NGO can view complaints, request to handle them, and work after approval. Admin assigns complaints, approves NGO requests, and monitors system performance.

Complaint includes title, description, media, location, priority, status, timeline, SLA, and timestamps. Status types are pending, in progress, resolved, and rejected.

Priority scoring is based on keywords, complaint age, base value, and interactions. Score ranges from zero to one hundred. Higher score means higher urgency.

SLA depends on priority. High priority has short deadline. Medium priority has moderate deadline. Low priority has longer deadline.

Tracking system shows status, timeline, updates, and actions. Timeline includes complaint creation, assignment, status changes, NGO involvement, and resolution.

NGO system works through requests. NGO sends request. Admin approves or rejects. Approved NGO gets access.

System uses APIs. Frontend sends request. Backend validates, processes logic, stores data, and returns response.

Security includes JWT authentication, password hashing, role based access, input validation, and secure uploads.

Architecture is frontend to API to backend to database to response.

System uses polling for updates. No real time websockets.

Limitations include basic AI, no real time updates, and manual NGO approval.

Core flow is complaint input, system processing, officer or NGO action, and final resolution.
"""

# ─── PROFESSIONAL CONFIG WITH KNOWLEDGE ───
professional_cfg = types.GenerateContentConfig(
    system_instruction=(
        "You are a professional AI assistant for the JanSamadhan platform. "
        "Use the following system knowledge to answer all queries correctly. "
        "Always give practical and helpful answers.\n\n"
        + KNOWLEDGE_BASE
    ),
    temperature=0.3,
    max_output_tokens=400,
)

# ─── API Endpoint ───
@router.post("/generate")
def generate_response(data: AIRequest):
    if not client:
        # Provide a local rule-based response fallback if AI is not configured
        query_lower = data.query.lower()
        if "login" in query_lower:
            fallback = "JanSamadhan: login requires a valid citizen or officer account. If your login isn't working, verify the email/password or make sure the database is running."
        elif "status" in query_lower or "complaint" in query_lower:
            fallback = "JanSamadhan: You can track your complaint status in the Citizen Dashboard or the Public Grievance section using the complaint ID."
        else:
            fallback = "JanSamadhan AI is currently offline. Please try again later or check system logs."
        return {
            "status": "success",
            "response": fallback,
            "answer": fallback
        }

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=data.query,
            config=professional_cfg
        )

        if not response or not response.text:
            raise HTTPException(status_code=500, detail="Empty AI response")

        return {
            "status": "success",
            "response": response.text,
            "answer": response.text # Added for backward compatibility with frontend
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
