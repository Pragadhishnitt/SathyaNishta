from fastapi import APIRouter

router = APIRouter()

@router.post("/investigate")
async def start_investigation():
    return {"status": "started"}
