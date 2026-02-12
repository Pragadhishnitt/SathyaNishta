from fastapi import APIRouter, Body

from app.orchestration.supervisor import Supervisor

router = APIRouter()

@router.post("/investigate")
async def start_investigation(payload: dict = Body(default_factory=dict)):
    supervisor = Supervisor()
    result = await supervisor.ainvoke({"input": payload})
    return {"status": "started", "workflow": "langgraph", "result": result}
