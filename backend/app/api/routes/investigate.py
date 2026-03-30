"""Investigation API routes — Live LangGraph SSE streaming.

POST /investigate       → creates investigation, starts async LangGraph run
GET  /investigate/{id}/stream  → SSE events from real agent execution
GET  /investigate/{id}  → final investigation result
"""

import asyncio
import json
import re
import uuid
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlmodel import Session

from app.core.config import settings
from app.shared.logger import setup_logger

router = APIRouter()
_logger = setup_logger("investigate_route")

# Init DB engine
engine = create_engine(settings.DATABASE_URL)

# In-memory queues for SSE streaming (per investigation)
_queues: Dict[str, asyncio.Queue] = {}
# In-memory results store (per investigation)
_results: Dict[str, dict] = {}


class InvestigationRequest(BaseModel):
    query: str
    mode: str = "standard"


def _extract_company_name(query: str) -> str:
    """Extract company name from investigation query using pattern matching."""
    # Try common patterns
    patterns = [
        r"(?:investigate|analyze|check|research|look into)\s+(.+?)(?:\s+for|\s+regarding|\s*$)",
        r"(?:about|on)\s+(.+?)(?:\s+for|\s+regarding|\s*$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up trailing words
            name = re.sub(
                r"\s+(circular|fraud|trading|financial|irregularities|violations|compliance).*$",
                "",
                name,
                flags=re.IGNORECASE,
            )
            if name and len(name) > 1:
                return name
    return "Unknown_Entity"

    # Fallback: look for capitalized words that look like company names
    words = query.split()
    capitalized = [
        w
        for w in words
        if w[0].isupper()
        and w.lower()
        not in {
            "investigate",
            "analyze",
            "check",
            "for",
            "the",
            "and",
            "in",
            "of",
            "about",
            "tell",
            "me",
            "what",
            "how",
            "is",
            "are",
            "do",
            "does",
        }
    ]
    if capitalized:
        return " ".join(capitalized)

    # Additional fallback: common company names and variations
    common_companies = [
        "Apple",
        "Apple Inc",
        "AAPL",
        "Apple Inc.",
        "Reliance",
        "Reliance Industries",
        "RELIAN",
        "SBI",
        "State Bank of India",
        "Wipro",
        "WIPRO",
        "Infosys",
        "INFOSY",
        "Hindustan Unilever",
        "HUL",
        "HindustanUnilever",
    ]

    # Check if any common company name is in the query
    for company in common_companies:
        if company.lower() in query.lower():
            return company

    return "Unknown Company"


@router.post("/investigate", status_code=202)
async def start_investigation(req: InvestigationRequest):
    inv_id = str(uuid.uuid4())
    company = _extract_company_name(req.query)

    _logger.info(f"Starting investigation {inv_id}: company={company}, mode={req.mode}")

    # Create SSE queue for this investigation
    _queues[inv_id] = asyncio.Queue()

    # Initial DB insert
    try:
        with Session(engine) as session:
            session.execute(
                text(
                    """
                    INSERT INTO investigations (id, query, status, created_at, updated_at)
                    VALUES (:id, :query, 'running', NOW(), NOW())
                """
                ),
                {"id": inv_id, "query": req.query},
            )
            session.commit()
    except Exception as e:
        _logger.error(f"Failed to create investigation in DB for {inv_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create investigation")

    # Start the LangGraph run in background
    asyncio.create_task(_run_investigation(inv_id, company, req.query, req.mode))

    return {
        "investigation_id": inv_id,
        "company_name": company,
        "stream_url": f"/api/investigate/{inv_id}/stream",
    }


async def _run_investigation(inv_id: str, company: str, query: str, mode: str):
    """Run the LangGraph investigation and push SSE events to the queue."""
    q = _queues[inv_id]

    try:
        from app.orchestration.langgraph_workflow import build_investigation_graph

        graph = build_investigation_graph()
        initial_state = {
            "investigation_id": inv_id,
            "company_name": company,
            "query": query,
            "mode": mode,
            "messages": [],
            "iteration_count": 0,
            "investigation_complete": False,
        }

        _logger.info(f"[{inv_id}] Starting LangGraph execution for {company}")

        # Track which agents have started
        agent_names = {
            "financial",
            "graph",
            "compliance",
            "audio",
            "news",
            "reflection",
            "synthesis",
        }
        final_state: Dict[str, object] = {}

        # Stream node-level updates from LangGraph
        async for event in graph.astream(initial_state, stream_mode="updates"):
            node_name = list(event.keys())[0]
            node_data = list(event.values())[0]
            if isinstance(node_data, dict):
                final_state.update(node_data)

            _logger.info(f"[{inv_id}] Node completed: {node_name}")

            if node_name == "supervisor":
                # Emit agent_start for the next agent being routed to
                next_agent = node_data.get("next_agent", "")
                if next_agent and next_agent in agent_names and next_agent != "synthesis":
                    await q.put(
                        {
                            "event": "agent_start",
                            "data": {
                                "agent": next_agent,
                                "timestamp": f"T+{node_data.get('iteration_count', 0)}s",
                            },
                        }
                    )

            elif node_name in ("financial", "graph", "compliance", "audio", "news"):
                # Agent completed — emit agent_done with findings
                findings_key = f"{node_name}_findings"
                findings = node_data.get(findings_key, {})
                event_payload = {
                    "agent": node_name,
                    "risk_score": findings.get("risk_score", 0),
                    "findings": findings.get("findings", [])[:5],  # limit to 5 for SSE
                    "evidence_map": findings.get("evidence", {}),
                }

                if node_name == "graph":
                    event_payload["graph_data"] = node_data.get("graph_payload", {"nodes": [], "edges": []})
                if node_name == "audio":
                    timeline = node_data.get("audio_timeline", []) or []
                    event_payload["deception_markers"] = [
                        {
                            "start": round(float(m.get("start_pct", 0)) * 100, 2),
                            "end": round(float(m.get("end_pct", 0)) * 100, 2),
                            "label": m.get("explanation", m.get("marker_type", "Marker")),
                            "severity": m.get("severity", "medium"),
                            "quote": m.get("quote", ""),
                            "marker_type": m.get("marker_type", ""),
                            "start_time_s": m.get("start_time_s", 0),
                            "end_time_s": m.get("end_time_s", 0),
                        }
                        for m in timeline
                    ]
                    event_payload["audio_timeline_total_duration_s"] = node_data.get("audio_timeline_total_duration_s", 0)

                await q.put(
                    {
                        "event": "agent_done",
                        "data": event_payload,
                    }
                )

            elif node_name == "reflection":
                # Reflection results treated as an agent so UI renders it
                await q.put(
                    {
                        "event": "agent_done",
                        "data": {
                            "agent": "reflection",
                            "risk_score": None,  # Don't show delta as absolute score
                            "findings": [node_data.get("reflection_notes", "")],
                            "evidence_map": {"passed": ("Yes" if node_data.get("reflection_passed") else "No")},
                        },
                    }
                )

            elif node_name == "synthesis":
                # Final synthesis
                synthesis_data = {
                    "company_name": company,
                    "fraud_risk_score": node_data.get("fraud_risk_score", 0),
                    "verdict": node_data.get("verdict", "SAFE"),
                    "evidence": node_data.get("evidence", [])[:15],  # limit for SSE
                    "financial_findings": final_state.get("financial_findings", {}),
                    "graph_findings": final_state.get("graph_findings", {}),
                    "compliance_findings": final_state.get("compliance_findings", {}),
                    "audio_findings": final_state.get("audio_findings", {}),
                    "news_findings": final_state.get("news_findings", {}),
                    "graph_payload": final_state.get("graph_payload", {"nodes": [], "edges": []}),
                    "audio_timeline": final_state.get("audio_timeline", []),
                    "audio_timeline_total_duration_s": final_state.get("audio_timeline_total_duration_s", 0),
                }
                await q.put({"event": "synthesis", "data": synthesis_data})

                # Store final result
                _results[inv_id] = {
                    "investigation_id": inv_id,
                    "company_name": company,
                    "query": query,
                    "mode": mode,
                    **synthesis_data,
                    "financial_findings": final_state.get("financial_findings", {}),
                    "graph_findings": final_state.get("graph_findings", {}),
                    "compliance_findings": final_state.get("compliance_findings", {}),
                    "audio_findings": final_state.get("audio_findings", {}),
                    "news_findings": final_state.get("news_findings", {}),
                    "graph_payload": final_state.get("graph_payload", {"nodes": [], "edges": []}),
                    "audio_timeline": final_state.get("audio_timeline", []),
                    "audio_timeline_total_duration_s": final_state.get("audio_timeline_total_duration_s", 0),
                }

        # Mark complete
        await q.put({"event": "complete", "data": {"investigation_id": inv_id}})
        _logger.info(f"[{inv_id}] Investigation complete")

        # Update DB
        try:
            with Session(engine) as session:
                session.execute(
                    text(
                        """
                        UPDATE investigations 
                        SET status = 'completed', 
                            fraud_risk_score = :score, 
                            verdict = :verdict, 
                            updated_at = NOW(),
                            completed_at = NOW() 
                        WHERE id = :id
                    """
                    ),
                    {
                        "id": inv_id,
                        "score": synthesis_data["fraud_risk_score"],
                        "verdict": synthesis_data["verdict"],
                    },
                )
                session.commit()

            with Session(engine) as session:
                session.execute(
                    text(
                        """
                        INSERT INTO audit_trails (investigation_id, step_type, timestamp, output_payload)
                        VALUES (:inv_id, 'synthesis', NOW(), :output)
                    """
                    ),
                    {"inv_id": inv_id, "output": json.dumps(synthesis_data)},
                )
                session.commit()
        except Exception as e:
            _logger.error(
                f"Failed to persist final investigation state for {inv_id}: {e}",
                exc_info=True,
            )

    except Exception as e:
        _logger.error(f"[{inv_id}] Investigation failed: {e}")
        await q.put(
            {
                "event": "error",
                "data": {"message": str(e)[:200]},
            }
        )
        await q.put({"event": "complete", "data": {"investigation_id": inv_id}})

        # Mark failed in DB
        try:
            with Session(engine) as session:
                session.execute(
                    text("UPDATE investigations SET status = 'failed' WHERE id = :id"),
                    {"id": inv_id},
                )
                session.commit()
        except Exception as db_e:
            _logger.error(f"Failed to update failed investigation in DB: {db_e}")


@router.get("/investigate/{inv_id}/stream")
async def stream_investigation(inv_id: str):
    """SSE stream of investigation events."""
    if inv_id not in _queues:
        raise HTTPException(status_code=404, detail="Investigation not found")

    q = _queues[inv_id]

    async def event_generator():
        try:
            while True:
                # Wait for next event with timeout
                try:
                    item = await asyncio.wait_for(q.get(), timeout=300)
                except asyncio.TimeoutError:
                    yield 'event: error\ndata: {"message": "Investigation timed out"}\n\n'
                    break

                yield f"event: {item['event']}\ndata: {json.dumps(item['data'])}\n\n"

                if item["event"] == "complete":
                    break
        finally:
            # Cleanup queue after stream ends
            _queues.pop(inv_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/investigate/{inv_id}")
async def get_investigation(inv_id: str):
    """Get the final result of a completed investigation."""
    if inv_id in _results:
        return _results[inv_id]

    try:
        with Session(engine) as session:
            inv = session.execute(
                text("SELECT id, query, status FROM investigations WHERE id = :id"),
                {"id": inv_id},
            ).fetchone()

            if not inv:
                raise HTTPException(status_code=404, detail="Investigation not found")

            if inv.status == "completed":
                audit = session.execute(
                    text(
                        "SELECT output_payload FROM audit_trails WHERE investigation_id = :id AND step_type = 'synthesis' ORDER BY timestamp DESC LIMIT 1"
                    ),
                    {"id": inv_id},
                ).fetchone()

                if audit and audit.output_payload:
                    payload = (
                        json.loads(audit.output_payload) if isinstance(audit.output_payload, str) else audit.output_payload
                    )
                    payload["investigation_id"] = inv_id
                    _results[inv_id] = payload
                    return payload

    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to fetch investigation {inv_id} from DB: {e}")

    raise HTTPException(status_code=404, detail="Investigation not found or still running")
