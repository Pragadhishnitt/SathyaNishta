from pydantic import BaseModel
from typing import Optional


class InvestigationRequest(BaseModel):
    query: str
    mode: str = "standard"


class InvestigationResponse(BaseModel):
    investigation_id: str
    stream_url: str
