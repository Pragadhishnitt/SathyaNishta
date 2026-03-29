from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

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
    investigation_context: Dict[str, Any] | None = None


@router.post("/chat")
async def chat_standard(request: ChatRequest):
    """Chat endpoint supporting both standard and evidence-grounded forensic modes."""
    _logger.info(
        f"Incoming chat request: {len(request.messages)} messages, context={'present' if request.investigation_context else 'none'}"
    )

    try:
        client = get_portkey_client()

        # Format messages for Portkey
        formatted_messages = [{"role": m.role, "content": m.content} for m in request.messages]
        _logger.debug(f"Formatted {len(formatted_messages)} messages for Portkey")

        if request.investigation_context:
            ctx = request.investigation_context
            evidence = ctx.get("evidence", [])
            evidence_lines = "\n".join(
                [f"[{e.get('severity', 'N/A')}] {e.get('source', 'Unknown')}: {e.get('finding', '')}" for e in evidence]
            )
            system_content = (
                "You are SathyaNishta's forensic investigation assistant.\n"
                "Answer only using the provided investigation evidence.\n"
                "Cite sources explicitly (e.g., 'According to the Graph Agent...').\n"
                "If evidence is missing, state that clearly and do not fabricate.\n\n"
                f"COMPANY: {ctx.get('company_name', 'Unknown')}\n"
                f"VERDICT: {ctx.get('verdict', 'Unknown')}\n"
                f"FRAUD RISK SCORE: {ctx.get('fraud_risk_score', 'N/A')}/10\n\n"
                f"EVIDENCE SUMMARY:\n{evidence_lines}\n\n"
                "DETAILED FINDINGS:\n"
                f"financial={ctx.get('financial_findings', {})}\n"
                f"graph={ctx.get('graph_findings', {})}\n"
                f"compliance={ctx.get('compliance_findings', {})}\n"
                f"audio={ctx.get('audio_findings', {})}\n"
                f"news={ctx.get('news_findings', {})}\n"
            )
        else:
            system_content = (
                "You are MarketChatGPT by ET. You provide concise, data-driven insights "
                "about stock markets, companies, and economy. IMPORTANT: Always format your "
                "response using professional markdown (bolding, lists, etc). At the end of every "
                "response, ALWAYS add a line: '*Note: Use SathyaNishta Mode for in-depth forensic "
                "investigation and multi-agent fraud analysis.*'"
            )

        _logger.debug(f"Generated system prompt length: {len(system_content)}")
        system_msg = {"role": "system", "content": system_content}

        @retry(
            wait=wait_exponential(multiplier=1, min=2, max=10),
            stop=stop_after_attempt(3),
            reraise=True,
        )
        def call_portkey():
            _logger.info("Calling Portkey chat.completions.create (with retries)...")
            return client.chat.completions.create(messages=[system_msg] + formatted_messages, stream=False)

        response = call_portkey()
        _logger.info("Portkey response received")

        # Robust content extraction (handles both object and dict responses)
        content = None
        try:
            if hasattr(response, "choices"):
                content = response.choices[0].message.content
            else:
                content = response.get("choices", [{}])[0].get("message", {}).get("content")
        except Exception as exc:
            _logger.error(f"Failed to extract content from Portkey response: {exc}")
            content = str(response)

        _logger.info(f"Returning chat response: {len(content) if content else 0} chars")
        return {"role": "assistant", "content": content}
    except Exception as e:
        _logger.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
