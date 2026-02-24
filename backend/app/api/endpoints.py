from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any

from app.services.router_service import get_router_service

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 1.0

@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    router_service = get_router_service()
    
    # Extract the last user message
    last_user_message = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
    
    if not last_user_message:
        raise HTTPException(status_code=400, detail="No user message found.")

    response_content = await router_service.route_query(last_user_message, model_hint=request.model)
    
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response_content,
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 9,
            "completion_tokens": len(response_content.split()),
            "total_tokens": 9 + len(response_content.split())
        }
    }

@router.get("/stats")
async def get_stats():
    router_service = get_router_service()
    savings = router_service.total_cost_theoretical - router_service.total_cost_actual
    return {
        "queries_count": router_service.queries_count,
        "total_cost_actual": router_service.total_cost_actual,
        "total_cost_theoretical": router_service.total_cost_theoretical,
        "savings": savings,
        "accuracy_estimate": "95%"
    }
