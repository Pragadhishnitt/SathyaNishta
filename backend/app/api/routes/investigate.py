"""Investigation API routes — Sprint 1.

POST /investigate  → returns investigation_id + stream_url
GET  /investigate/{inv_id}/stream → SSE mock events (Sprint 1)
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import asyncio
import json
import uuid

router = APIRouter()


class InvestigationRequest(BaseModel):
    query: str
    mode: str = "standard"


@router.post("/investigate", status_code=202)
async def start_investigation(req: InvestigationRequest):
    inv_id = str(uuid.uuid4())
    return {
        "investigation_id": inv_id,
        "stream_url": f"/api/investigate/{inv_id}/stream",
    }


@router.get("/investigate/{inv_id}/stream")
async def stream_investigation(inv_id: str):
    """Sprint 1: mock SSE events so frontend can wire against real transport."""
    mock_events = [
        ("agent_start",  {"agent": "financial",  "timestamp": "T+0s"}),
        ("agent_done",   {"agent": "financial",  "risk_score": 7.2,
                          "findings": ["Cash/EBITDA 0.20", "RPT 50% of revenue"]}),
        ("agent_start",  {"agent": "graph",      "timestamp": "T+4s"}),
        ("agent_done",   {"agent": "graph",      "risk_score": 9.1,
                          "findings": ["3-node circular loop", "₹1,440 Cr flow"]}),
        ("agent_start",  {"agent": "compliance", "timestamp": "T+8s"}),
        ("agent_done",   {"agent": "compliance", "risk_score": 8.0,
                          "findings": ["SEBI LODR Reg 23 breach", "Companies Act §188"]}),
        ("reflection",   {"passed": True, "notes": "All findings verified"}),
        ("synthesis",    {"fraud_risk_score": 8.7, "verdict": "CRITICAL",
                          "evidence": [
                              {"source": "Financial", "finding": "Cash/EBITDA 0.20", "severity": "HIGH"},
                              {"source": "Graph",     "finding": "3 circular loops, ₹1440 Cr", "severity": "CRITICAL"},
                              {"source": "Compliance", "finding": "SEBI LODR Reg 23 breach", "severity": "HIGH"},
                          ]}),
        ("complete",     {"investigation_id": inv_id}),
    ]

    async def event_generator():
        for event_type, data in mock_events:
            yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(1.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
