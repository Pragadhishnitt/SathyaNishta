from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.financial.agent import FinancialAgent


class SupervisorState(TypedDict, total=False):
    """Minimal state passed through the LangGraph workflow.

    This is intentionally tiny (bare workflow, no business logic yet).
    Extend this as you introduce routing, tools, and agent outputs.
    """

    investigation_id: str
    input: Dict[str, Any]
    events: List[Dict[str, Any]]


async def _supervisor_entry(state: SupervisorState) -> SupervisorState:
    # Minimal demo wiring: call a single agent through Portkey.
    agent = FinancialAgent()
    payload = state.get("input") or {}

    content = await agent.aprocess(payload)
    events = list(state.get("events") or [])
    events.append({"type": "agent_result", "agent": "financial", "content": content})

    state["events"] = events
    return state


def build_workflow():
    """Builds and compiles the minimal LangGraph workflow.

    Supervisor is the entry node and immediately terminates.
    """

    graph = StateGraph(SupervisorState)
    graph.add_node("supervisor", _supervisor_entry)

    graph.add_edge(START, "supervisor")
    graph.add_edge("supervisor", END)

    return graph.compile()
