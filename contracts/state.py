"""Frozen InvestigationState contract — Sprint 0.

Both Team A (orchestration) and Team B (agents, frontend) depend on this.
Do NOT modify without joint sign-off.
"""

from typing import TypedDict, List, Dict, Annotated, Literal
import operator


class AgentFinding(TypedDict):
    risk_score: float           # 0–10
    findings:   List[str]       # human-readable flags
    evidence:   Dict[str, str]  # { metric_name: value_with_source }


class InvestigationState(TypedDict, total=False):
    # ── Input ──────────────────────────────────────────────────────
    investigation_id: str
    company_name:     str
    query:            str
    mode:             Literal["standard", "sathyanishta"]

    # ── Agent findings (Team B writes, Team A reads) ────────────────
    financial_findings:  AgentFinding
    graph_findings:      AgentFinding
    graph_payload:       Dict
    audio_findings:      AgentFinding
    audio_timeline:      List[Dict]
    audio_timeline_total_duration_s: float
    compliance_findings: AgentFinding
    news_findings:       AgentFinding

    # ── Reflection gate (Team A writes, Team B reads for UI) ────────
    reflection_passed:   bool
    reflection_notes:    str

    # ── Orchestration (Team A owns) ─────────────────────────────────
    messages:            Annotated[List[str], operator.add]
    next_agent:          str
    iteration_count:     int
    investigation_complete: bool

    # ── Final output (Team A synthesizes, Team B renders) ───────────
    fraud_risk_score: float     # 0–10 weighted
    verdict:          str       # SAFE | CAUTION | HIGH_RISK | CRITICAL
    evidence:         List[Dict]
    audit_trail:      List[Dict]
