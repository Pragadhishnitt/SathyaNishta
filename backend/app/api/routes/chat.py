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
            "content": "You are MarketChatGPT by ET. You provide concise, data-driven insights about stock markets, companies, and economy. IMPORTANT: Always format your response using professional markdown (bolding, lists, etc). At the end of every response, ALWAYS add a line: '*Note: Use SathyaNishta Mode for in-depth forensic investigation and multi-agent fraud analysis.*'"
        }
        
        response = client.chat.completions.create(
            messages=[system_msg] + formatted_messages,
            stream=False
        )
        
        # Robust content extraction (handles both object and dict responses)
        content = None
        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError):
            try:
                content = response.get("choices", [{}])[0].get("message", {}).get("content")
            except Exception:
                content = str(response)

        return {
            "role": "assistant",
            "content": content
        }
    except Exception as e:
        _logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
