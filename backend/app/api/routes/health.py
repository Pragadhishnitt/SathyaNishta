import time

from fastapi import APIRouter

from app.shared.config import config
from app.shared.llm_portkey import PortkeyLLMError, chat_complete

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/health/llm")
async def llm_health_check():
    """Verifies Portkey gateway connectivity + routing.

    This makes a small chat completion request through Portkey.
    """

    started = time.monotonic()
    try:
        result = chat_complete(
            user_prompt="Reply with a single word: pong",
            system_prompt="You are a health check endpoint.",
            temperature=0,
            metadata={"route": "health_llm"},
        )
        elapsed_ms = int((time.monotonic() - started) * 1000)
        content = (result.get("content") or "").strip()
        return {
            "status": "ok",
            "portkey": {
                "config": config.PORTKEY_CONFIG,
                "model": result.get("model"),
            },
            "latency_ms": elapsed_ms,
            "reply": content[:50],
        }
    except PortkeyLLMError as e:
        elapsed_ms = int((time.monotonic() - started) * 1000)
        return {
            "status": "error",
            "error": str(e),
            "portkey": {"config": config.PORTKEY_CONFIG},
            "latency_ms": elapsed_ms,
        }
    except Exception as e:
        elapsed_ms = int((time.monotonic() - started) * 1000)
        return {
            "status": "error",
            "error": f"LLM healthcheck failed: {type(e).__name__}",
            "portkey": {"config": config.PORTKEY_CONFIG},
            "latency_ms": elapsed_ms,
        }
