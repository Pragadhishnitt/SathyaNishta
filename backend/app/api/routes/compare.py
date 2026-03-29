from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json
import uuid
from typing import Dict, List, Optional

from app.shared.logger import setup_logger
from app.api.routes.investigate import _run_investigation, _extract_company_name, _queues

router = APIRouter(prefix="/api/compare", tags=["compare"])
_logger = setup_logger("compare_route")

class CompareRequest(BaseModel):
    company_a: str
    company_b: str
    mode: str = "sathyanishta"

@router.post("", status_code=202)
async def start_comparison(req: CompareRequest):
    comp_id = str(uuid.uuid4())
    inv_id_a = str(uuid.uuid4())
    inv_id_b = str(uuid.uuid4())
    
    _logger.info(f"Starting comparison {comp_id}: {req.company_a} vs {req.company_b}")
    
    # Initialize queues for both investigations (reuse existing investigate logic)
    _queues[inv_id_a] = asyncio.Queue()
    _queues[inv_id_b] = asyncio.Queue()
    
    # Create a unified comparison queue
    compare_queue = asyncio.Queue()
    _queues[comp_id] = compare_queue
    
    # Start both investigations in background
    asyncio.create_task(_run_investigation(inv_id_a, req.company_a, f"Investigate {req.company_a}", req.mode))
    asyncio.create_task(_run_investigation(inv_id_b, req.company_b, f"Investigate {req.company_b}", req.mode))
    
    # Start comparison monitor
    asyncio.create_task(_monitor_and_synthesize_comparison(comp_id, inv_id_a, inv_id_b, req.company_a, req.company_b))
    
    return {
        "comparison_id": comp_id,
        "investigation_id_a": inv_id_a,
        "investigation_id_b": inv_id_b,
        "stream_url": f"/api/compare/{comp_id}/stream"
    }

async def _monitor_and_synthesize_comparison(comp_id: str, id_a: str, id_b: str, name_a: str, name_b: str):
    """Monitor two investigations and emit interleaved events + final comparison synthesis."""
    q_comp = _queues[comp_id]
    q_a = _queues[id_a]
    q_b = _queues[id_b]
    
    done_a = False
    done_b = False
    
    # Track results for final synthesis
    result_a = None
    result_b = None
    
    async def forward_events(target_id: str, source_queue: asyncio.Queue, prefix: str):
        nonlocal done_a, done_b, result_a, result_b
        while True:
            item = await source_queue.get()
            
            # DON'T forward "complete" events from individual investigations
            # Only forward the final "complete" after both are done and comparison is ready
            if item["event"] == "complete":
                if prefix == "A": done_a = True
                else: done_b = True
                break
            
            # Wrap and forward all other events for comparison stream
            wrapped = {
                "event": item["event"],
                "data": {**item["data"], "company_slot": prefix}
            }
            await q_comp.put(wrapped)
            
            if item["event"] == "synthesis":
                if prefix == "A": result_a = item["data"]
                else: result_b = item["data"]
                
    # Run forwarders
    await asyncio.gather(
        forward_events(id_a, q_a, "A"),
        forward_events(id_b, q_b, "B")
    )
    
    # Perform Comparison Synthesis
    _logger.info(f"[{comp_id}] Both investigations complete. Running comparison synthesis.")
    try:
        from app.shared.llm_portkey import chat_complete
        
        comparison_prompt = f"""Compare these two companies based on their forensic findings.
        
        Company A ({name_a}): {json.dumps(result_a.get('evidence', [])[:5]) if result_a else 'N/A'}
        Risk Score A: {result_a.get('fraud_risk_score', 0) if result_a else 'N/A'}
        
        Company B ({name_b}): {json.dumps(result_b.get('evidence', [])[:5]) if result_b else 'N/A'}
        Risk Score B: {result_b.get('fraud_risk_score', 0) if result_b else 'N/A'}
        
        Highlight:
        1. Which company has higher risk and why?
        2. Are there common anomalies (e.g. both have circular loops)?
        3. Key differentiator in their fraud profile.
        
        Output JSON only: {{"comparison_summary": "...", "winner_on_reliability": "...", "key_risks_compared": "..."}}
        """
        
        res = chat_complete(user_prompt=comparison_prompt, system_prompt="Compare financial fraud profiles. JSON only.")
        content = res.get("content", "{}")
        if "```json" in content: content = content.split("```json")[-1].split("```")[0].strip()
        elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
        
        comparison_data = json.loads(content)
        await q_comp.put({"event": "comparison_synthesis", "data": comparison_data})
    except Exception as e:
        _logger.error(f"Comparison synthesis failed: {e}")
    
    await q_comp.put({"event": "complete", "data": {"comparison_id": comp_id}})

@router.get("/{comp_id}/stream")
async def stream_comparison(comp_id: str):
    if comp_id not in _queues:
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    q = _queues[comp_id]
    
    async def event_generator():
        try:
            while True:
                try:
                    item = await asyncio.wait_for(q.get(), timeout=300)
                    yield f"event: {item['event']}\ndata: {json.dumps(item['data'])}\n\n"
                    if item["event"] == "complete": break
                except asyncio.TimeoutError:
                    yield "event: error\ndata: {\"message\": \"Comparison timed out\"}\n\n"
                    break
        finally:
            _queues.pop(comp_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )
