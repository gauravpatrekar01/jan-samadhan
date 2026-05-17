import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.ai_service import ai_service

logger = logging.getLogger(__name__)

# Router
router = APIRouter()

# ─── Request schema ───
class AIRequest(BaseModel):
    query: str

# ─── API Endpoint ───
@router.post("/generate")
async def generate_response(data: AIRequest):
    """
    Ultra-fast, database-aware, multi-key intelligent chatbot endpoint.
    Uses async architecture to minimize latency.
    """
    if not data.query or not data.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    try:
        # Offload all logic to the async AI service
        result = await ai_service.process_query(data.query)
        
        # Backward compatibility with frontend expecting 'answer' instead of 'response'
        if "response" in result and "answer" not in result:
            result["answer"] = result["response"]
            
        return result
        
    except Exception as e:
        logger.error(f"Chatbot endpoint error: {e}")
        # Always return a structured fallback response on top-level failure
        return {
            "status": "error",
            "provider": "fallback_error",
            "response": "JanSamadhan AI is currently experiencing difficulties. Please try again later.",
            "answer": "JanSamadhan AI is currently experiencing difficulties. Please try again later.",
            "response_time_ms": 0
        }
