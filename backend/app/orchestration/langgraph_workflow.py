"""LangGraph investigation workflow — Sprint 1.

Multi-node graph: supervisor → agents → synthesis → END.
Supervisor uses deterministic routing (no LLM call) to walk through
agents in order. Each agent node returns mock AgentFinding stubs.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

# Ensure repo root is on sys.path so `contracts.state` resolves
_repo_root = str(Path(__file__).resolve().parents[3])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from contracts.state import InvestigationState
from app.agents.nodes import (
    audio_node,
    compliance_node,
    financial_node,
    graph_node,
    news_node,
    reflection_node,
    synthesis_node,
)


# Agent execution order per mode
STANDARD_SEQUENCE = ["financial", "graph", "compliance"]
SATHYANISHTA_SEQUENCE = ["financial", "graph", "compliance", "audio", "news", "reflection"]


def _supervisor_node(state: InvestigationState) -> Dict[str, Any]:
    """Deterministic routing: pick the next unfinished agent in sequence.

    Checks which agents have already posted findings and routes to the next
    one. Returns ``next_agent = "synthesis"`` once all required agents are done.
    """
    mode = state.get("mode", "standard")
    sequence = SATHYANISHTA_SEQUENCE if mode == "sathyanishta" else STANDARD_SEQUENCE

    # Map of agent name → state key that proves it ran
    done_keys = {
        "financial": "financial_findings",
        "graph": "graph_findings",
        "compliance": "compliance_findings",
        "audio": "audio_findings",
        "news": "news_findings",
        "reflection": "reflection_passed",
    }

    for agent in sequence:
        key = done_keys[agent]
        if state.get(key) is None:
            return {
                "next_agent": agent,
                "iteration_count": state.get("iteration_count", 0) + 1,
                "messages": [f"Supervisor → {agent}: routing next"],
            }

    # All done → go to synthesis
    return {
        "next_agent": "synthesis",
        "iteration_count": state.get("iteration_count", 0) + 1,
        "messages": ["Supervisor → synthesis: all agents complete"],
    }


def _route_next(state: InvestigationState) -> str:
    """Conditional edge: read next_agent from state."""
    return state.get("next_agent", "synthesis")


def build_investigation_graph():
    """Build and compile the full investigation StateGraph."""
    graph = StateGraph(InvestigationState)

    # Nodes
    graph.add_node("supervisor", _supervisor_node)
    graph.add_node("financial", financial_node)
    graph.add_node("graph", graph_node)
    graph.add_node("compliance", compliance_node)
    graph.add_node("audio", audio_node)
    graph.add_node("news", news_node)
    graph.add_node("reflection", reflection_node)
    graph.add_node("synthesis", synthesis_node)

    # Entry
    graph.add_edge(START, "supervisor")

    # Supervisor routes conditionally
    graph.add_conditional_edges(
        "supervisor",
        _route_next,
        {
            "financial": "financial",
            "graph": "graph",
            "compliance": "compliance",
            "audio": "audio",
            "news": "news",
            "reflection": "reflection",
            "synthesis": "synthesis",
        },
    )

    # Each agent loops back to supervisor
    for agent in ["financial", "graph", "compliance", "audio", "news", "reflection"]:
        graph.add_edge(agent, "supervisor")

    # Synthesis terminates the graph
    graph.add_edge("synthesis", END)

    return graph.compile()
