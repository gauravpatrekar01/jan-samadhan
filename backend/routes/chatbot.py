from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from dependencies import get_current_user_optional
from services.chatbot_service import chatbot_reply

router = APIRouter()


class ChatbotQuery(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)


@router.post("/query")
def query_chatbot(payload: ChatbotQuery, user: dict | None = Depends(get_current_user_optional)):
    result = chatbot_reply(payload.query)
    if user:
        result["user_role"] = user.get("role")
    return {"success": True, "data": result}

