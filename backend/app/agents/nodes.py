"""LangGraph node functions — bridge between class-based agents and the graph.

Sprint 1: all nodes return mock AgentFinding stubs.
Sprint 2+: swap stubs for real agent.process() calls.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

# Ensure the repo root is on sys.path so `contracts.state` resolves
_repo_root = str(Path(__file__).resolve().parents[3])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from contracts.state import AgentFinding, InvestigationState


# ── Agent node functions ────────────────────────────────────────


def financial_node(state: InvestigationState) -> Dict[str, Any]:
    """Sprint 1 stub — returns mock financial findings."""
    finding = AgentFinding(
        risk_score=7.2,
        findings=[
            "STUB: Cash/EBITDA anomaly detected (ratio 0.20, healthy range 0.6–0.8)",
            "STUB: Related party transactions 50% of revenue (SEBI LODR limit: 10%)",
        ],
        evidence={
            "cash_flow_ratio": "0.20 (source: mock)",
            "rpt_pct": "50% (source: mock)",
        },
    )
    return {
        "financial_findings": finding,
        "messages": [f"Financial Agent: stub complete (risk={finding['risk_score']})"],
    }


def graph_node(state: InvestigationState) -> Dict[str, Any]:
    """Sprint 1 stub — returns mock graph/circular-trading findings."""
    finding = AgentFinding(
        risk_score=9.1,
        findings=[
            "STUB: 3-node circular loop: Target → Shell A → Shell B → Target",
            "STUB: Total circular flow ₹1,440 Cr in Q3 2024",
            "STUB: Shared director on target + Shell A boards",
        ],
        evidence={
            "circular_loop": "Target → Shell A → Shell B → Target (source: mock)",
            "circular_flow": "₹1,440 Cr (source: mock)",
            "shared_director": "Director X on Target + Shell A (source: mock)",
        },
    )
    return {
        "graph_findings": finding,
        "messages": [f"Graph Agent: stub complete (risk={finding['risk_score']})"],
    }


def compliance_node(state: InvestigationState) -> Dict[str, Any]:
    """Sprint 1 stub — returns mock compliance findings."""
    finding = AgentFinding(
        risk_score=8.0,
        findings=[
            "STUB: SEBI LODR Reg 23 breach — RPT 50% > 10% threshold",
            "STUB: Companies Act §188 — circular transactions undisclosed",
        ],
        evidence={
            "sebi_lodr_reg23": "RPT 50% > 10% limit (source: mock)",
            "companies_act_188": "Undisclosed circular transactions (source: mock)",
        },
    )
    return {
        "compliance_findings": finding,
        "messages": [f"Compliance Agent: stub complete (risk={finding['risk_score']})"],
    }


def audio_node(state: InvestigationState) -> Dict[str, Any]:
    """Sprint 1 stub — returns mock audio findings."""
    finding = AgentFinding(
        risk_score=6.5,
        findings=[
            "STUB: Stress spike detected during revenue discussion",
            "STUB: Hedging language count above baseline",
        ],
        evidence={
            "stress_spike": "Revenue segment 2:30–3:15 (source: mock)",
            "hedging_count": "12 instances (source: mock)",
        },
    )
    return {
        "audio_findings": finding,
        "messages": [f"Audio Agent: stub complete (risk={finding['risk_score']})"],
    }


def reflection_node(state: InvestigationState) -> Dict[str, Any]:
    """Sprint 1 stub — always passes reflection."""
    return {
        "reflection_passed": True,
        "reflection_notes": "All findings cross-verified against source data (stub)",
        "messages": ["Reflection Agent: all findings verified (stub)"],
    }


def synthesis_node(state: InvestigationState) -> Dict[str, Any]:
    """Compute weighted fraud_risk_score + verdict from agent findings."""
    weights = {
        "financial": 0.25,
        "graph": 0.35,
        "compliance": 0.30,
        "audio": 0.10,
    }

    total_weight = 0.0
    weighted_sum = 0.0
    all_evidence = []

    for agent_key, weight in weights.items():
        findings_key = f"{agent_key}_findings"
        finding = state.get(findings_key)
        if finding and isinstance(finding, dict):
            score = finding.get("risk_score", 0.0)
            weighted_sum += score * weight
            total_weight += weight

            # Collect evidence for the final report
            for f in finding.get("findings", []):
                all_evidence.append({
                    "source": agent_key.title(),
                    "finding": f,
                    "severity": (
                        "CRITICAL" if score >= 8 else
                        "HIGH" if score >= 6 else
                        "MEDIUM" if score >= 4 else
                        "LOW"
                    ),
                })

    fraud_risk_score = round(weighted_sum / total_weight, 1) if total_weight > 0 else 0.0

    if fraud_risk_score >= 8:
        verdict = "CRITICAL"
    elif fraud_risk_score >= 6:
        verdict = "HIGH_RISK"
    elif fraud_risk_score >= 4:
        verdict = "CAUTION"
    else:
        verdict = "SAFE"

    return {
        "fraud_risk_score": fraud_risk_score,
        "verdict": verdict,
        "evidence": all_evidence,
        "investigation_complete": True,
        "messages": [f"Synthesis: score={fraud_risk_score}, verdict={verdict}"],
    }
