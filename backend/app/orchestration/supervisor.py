"""Orchestration entrypoint — thin wrapper around the LangGraph workflow."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.orchestration.langgraph_workflow import InvestigationState, build_investigation_graph

_graph = None


def _get_graph():
    """Lazy-compile the graph once."""
    global _graph
    if _graph is None:
        _graph = build_investigation_graph()
    return _graph


def invoke(state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _get_graph().invoke(state or {})


async def ainvoke(state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return await _get_graph().ainvoke(state or {})
