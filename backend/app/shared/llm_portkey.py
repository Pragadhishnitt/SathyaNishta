from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.shared.config import config


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
      - PORTKEY_VIRTUAL_KEY (routes to provider key stored in Portkey vault)
      - PORTKEY_CONFIG (config id or JSON; use to enable semantic cache/routing/fallbacks)
    """

    if not config.PORTKEY_API_KEY:
        raise PortkeyLLMError("Missing PORTKEY_API_KEY. Set it in your environment (.env / docker-compose).")

    from portkey_ai import Portkey  # local import to keep startup resilient if deps change

    kwargs: Dict[str, Any] = {"api_key": config.PORTKEY_API_KEY}

    if config.PORTKEY_VIRTUAL_KEY:
        kwargs["virtual_key"] = config.PORTKEY_VIRTUAL_KEY

    parsed_config = _parse_portkey_config(config.PORTKEY_CONFIG)
    if parsed_config is not None:
        kwargs["config"] = parsed_config

    return Portkey(**kwargs)


def chat_complete(
    *,
    user_prompt: str,
    system_prompt: str = "You are a helpful assistant.",
    model: Optional[str] = None,
    temperature: float = 0.2,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Performs a chat completion via Portkey.

    Returns a small normalized dict.
    """

    client = get_portkey_client()

    model_to_use = model or config.PORTKEY_MODEL or "gemini-1.5-flash"

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
        model=model_to_use,
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
        "model": model_to_use,
        "content": content,
        "raw": response,
    }
