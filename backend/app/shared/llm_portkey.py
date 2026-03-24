from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from tenacity import retry, wait_exponential, stop_after_attempt

from app.core.config import settings


class PortkeyLLMError(RuntimeError):
    pass


def _parse_portkey_config(raw: Optional[str]) -> Optional[object]:
    if not raw:
        return None

    candidate = raw.strip()
    if not candidate:
        return None

    # Portkey supports either a config id like "pc-***" or a config JSON object.
    if candidate.startswith("{"):
        return json.loads(candidate)
    return candidate


def get_portkey_client():
    """Returns a Portkey SDK client configured from env vars.

    Required:
      - PORTKEY_API_KEY

    Recommended:
      - PORTKEY_CONFIG_ID (config id created in Portkey UI; controls model, routing, fallbacks)
    """

    if not settings.PORTKEY_API_KEY:
        raise PortkeyLLMError("Missing PORTKEY_API_KEY. Set it in your environment (.env / docker-compose).")

    from portkey_ai import Portkey  # local import to keep startup resilient if deps change

    kwargs: Dict[str, Any] = {
        "api_key": settings.PORTKEY_API_KEY,
        "timeout": 60.0,
        "max_retries": 2,
    }

    parsed_config = _parse_portkey_config(settings.PORTKEY_CONFIG_ID)
    if parsed_config is not None:
        kwargs["config"] = parsed_config

    return Portkey(**kwargs)


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    reraise=True
)
def chat_complete(
    *,
    user_prompt: str,
    system_prompt: str = "You are a helpful assistant.",
    temperature: float = 0.2,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Performs a chat completion via Portkey.

    The model is determined by the Portkey Config (set in Portkey UI),
    not passed by callers.

    Returns a small normalized dict.
    """

    client = get_portkey_client()

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    request_client = client
    if metadata:
        # Portkey supports request-scoped options; keep payload OpenAI-compatible.
        try:
            request_client = client.with_options(metadata=metadata)
        except Exception:
            request_client = client

    response = request_client.chat.completions.create(
        messages=messages,
        temperature=temperature,
    )

    # Portkey SDK follows OpenAI-style response objects.
    content = None
    try:
        content = response.choices[0].message.content
    except Exception:
        # Fallback if response is dict-like
        content = (
            (response.get("choices") or [{}])[0]
            .get("message", {})
            .get("content")
        )

    return {
        "content": content,
        "raw": response,
    }
