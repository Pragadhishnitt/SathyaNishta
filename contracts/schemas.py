from pydantic import BaseModel

class InvestigationRequest(BaseModel):
    query: string
    user_id: string

class InvestigationResponse(BaseModel):
    status: string
    result: dict
