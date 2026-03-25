from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.shared.llm_portkey import get_portkey_client
from app.shared.logger import get_logger

router = APIRouter()
_logger = get_logger(__name__)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    stream: bool = False

@router.post("/chat")
async def chat_standard(request: ChatRequest):
    """Standard chat endpoint for MarketChatGPT using Portkey."""
    try:
        client = get_portkey_client()
        
        # Format messages for Portkey
        formatted_messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        # Add a system prompt for MarketChatGPT personality
        system_msg = {
            "role": "system", 
            "content": "You are MarketChatGPT by ET. You are a helpful AI financial assistant. You provide concise, data-driven insights about stock markets, companies, and economy. If the user asks for a deep forensic audit or fraud investigation, suggest they enable 'SathyaNishta Mode' for multi-agent analysis."
        }
        
        response = client.chat.completions.create(
            messages=[system_msg] + formatted_messages,
            stream=False # Keep it simple for now, can add streaming later if needed
        )
        
        return {
            "role": "assistant",
            "content": response.choices[0].message.content
        }
    except Exception as e:
        _logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
