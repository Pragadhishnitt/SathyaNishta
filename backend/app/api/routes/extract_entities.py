import json
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.shared.llm_portkey import chat_complete

router = APIRouter()


class ExtractEntitiesRequest(BaseModel):
    company_name: str
    evidence: List[Dict[str, Any]]


@router.post("/extract-entities")
async def extract_entities(req: ExtractEntitiesRequest):
    try:
        evidence_text = "\n".join([str(e.get("finding", "")) for e in req.evidence[:20]])
        prompt = (
            f"From these investigation findings for {req.company_name}, extract names of "
            "subsidiary companies, promoter entities, or shell companies mentioned.\n"
            'Return ONLY valid JSON: {"entities": ["Name1", "Name2"]}. Max 4 entities.\n'
            "Do not include the original company name.\n"
            f"Findings:\n{evidence_text[:1800]}"
        )

        response = chat_complete(
            user_prompt=prompt,
            system_prompt="Extract legal entity names from text. Output JSON only.",
            temperature=0.1,
            metadata={"route": "extract-entities"},
        )
        content = (response.get("content", "") or "").strip()
        if "```json" in content:
            content = content.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in content:
            content = content.split("```", 1)[1].split("```", 1)[0].strip()

        parsed = json.loads(content) if content else {}
        entities = parsed.get("entities", []) if isinstance(parsed, dict) else []
        if not isinstance(entities, list):
            entities = []

        normalized = []
        original_lower = req.company_name.lower().strip()
        for entity in entities:
            if not isinstance(entity, str):
                continue
            cleaned = entity.strip()
            if not cleaned:
                continue
            if cleaned.lower() == original_lower:
                continue
            normalized.append(cleaned)

        return {"entities": normalized[:4]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
