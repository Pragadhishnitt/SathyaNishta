from typing import Optional

from pydantic import BaseModel


class InvestigationRequest(BaseModel):
    query: str
    mode: str = "standard"


class InvestigationResponse(BaseModel):
    investigation_id: str
    stream_url: str
