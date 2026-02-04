"""
Sathya Nishta — Backend Contracts (Pydantic Schemas)
=====================================================
TEAM A OWNS THIS FILE.

All schemas used for:
- API requests/responses
- Agent task definitions
- Orchestration state
- Database models

Version: 1.0.0
Last Updated: Sprint 1
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, HttpUrl, ConfigDict

# ==========================================
# ENUMS
# ==========================================

class InvestigationStatus(str, Enum):
    """Status of an investigation lifecycle"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class AgentType(str, Enum):
    """Available specialist agent types"""
    FINANCIAL = "financial"
    GRAPH = "graph"
    AUDIO = "audio"
    COMPLIANCE = "compliance"


class AgentStatus(str, Enum):
    """Status of a single agent execution"""
    PENDING = "pending"
    RUNNING = "running"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class Severity(str, Enum):
    """Severity level for findings"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Verdict(str, Enum):
    """Final fraud risk verdict"""
    CRITICAL = "critical"  # Score 8-10
    HIGH = "high"          # Score 6-7.9
    MEDIUM = "medium"      # Score 4-5.9
    LOW = "low"            # Score 2-3.9
    SAFE = "safe"          # Score 0-1.9


# ==========================================
# SHARED MODELS
# ==========================================

class Finding(BaseModel):
    """A single finding from an agent"""
    type: str = Field(..., description="Classification (e.g., 'cash_flow_anomaly', 'circular_loop')")
    severity: Severity
    detail: str = Field(..., min_length=10, description="Human-readable description")
    evidence: str = Field(..., description="Source reference (doc name, page, timestamp)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Agent's confidence in this finding")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "cash_flow_divergence",
                "severity": "high",
                "detail": "EBITDA grew 15% but operating cash flow declined 8% YoY",
                "evidence": "Q3_2024_cashflow.pdf, page 4",
                "confidence": 0.92,
                "metadata": {"ebitda_growth": 15.0, "ocf_growth": -8.0}
            }
        }
    )


# ==========================================
# AGENT CONTRACTS
# ==========================================

class AgentTask(BaseModel):
    """Task sent from Supervisor to a specialist agent"""
    task_id: str = Field(default_factory=lambda: f"task_{uuid4().hex[:8]}")
    investigation_id: UUID
    agent_type: AgentType
    params: Dict[str, Any] = Field(..., description="Agent-specific parameters")
    priority: int = Field(default=1, ge=1, le=10)
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context from Supervisor")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "task_a1b2c3d4",
                "investigation_id": "123e4567-e89b-12d3-a456-426614174000",
                "agent_type": "financial",
                "params": {
                    "company_ticker": "ADANI",
                    "period": "Q3-2024",
                    "comparison_periods": ["Q2-2024", "Q3-2023"]
                },
                "priority": 1
            }
        }
    )


class AgentOutput(BaseModel):
    """Output returned by a specialist agent after execution"""
    task_id: str
    investigation_id: UUID
    agent_type: AgentType
    status: AgentStatus
    findings: List[Finding]
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence across all findings")
    execution_time_ms: int = Field(..., ge=0)
    model_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Token usage, model name, request ID from LLM provider"
    )

    @field_validator("status")
    def status_must_be_terminal(cls, v):
        """Agent output must have a terminal status"""
        if v not in [AgentStatus.APPROVED, AgentStatus.REJECTED, AgentStatus.FAILED]:
            raise ValueError(f"AgentOutput status must be terminal, got: {v}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "task_a1b2c3d4",
                "investigation_id": "123e4567-e89b-12d3-a456-426614174000",
                "agent_type": "financial",
                "status": "approved",
                "findings": [],
                "confidence": 0.87,
                "execution_time_ms": 4230,
                "model_metadata": {
                    "model": "gemini-1.5-flash",
                    "tokens_used": 3420,
                    "request_id": "req_abc123"
                }
            }
        }
    )


# ==========================================
# REFLECTION
# ==========================================

class ReflectionFeedback(BaseModel):
    """Specific feedback item when Reflection rejects an agent output"""
    field: str = Field(..., description="Which part of the output has issues (e.g., 'findings[0].detail')")
    issue: str = Field(..., description="What's wrong")
    action: str = Field(..., description="What the agent should do to fix it")


class ReflectionVerdict(BaseModel):
    """Reflection agent's decision on an agent output"""
    verdict: AgentStatus  # Must be APPROVED or REJECTED
    agent_type: AgentType
    task_id: str
    feedback: List[ReflectionFeedback] = Field(default_factory=list)
    reflection_confidence: float = Field(..., ge=0.0, le=1.0)

    @field_validator("verdict")
    def verdict_must_be_terminal(cls, v):
        if v not in [AgentStatus.APPROVED, AgentStatus.REJECTED]:
            raise ValueError(f"ReflectionVerdict must be APPROVED or REJECTED, got: {v}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "verdict": "rejected",
                "agent_type": "financial",
                "task_id": "task_a1b2c3d4",
                "feedback": [
                    {
                        "field": "findings[0].detail",
                        "issue": "Claim 'revenue grew 25%' contradicts source document showing 18%",
                        "action": "Re-query balance sheet and verify exact revenue figures"
                    }
                ],
                "reflection_confidence": 0.95
            }
        }
    )


# ==========================================
# ORCHESTRATION
# ==========================================

class InvestigationPlan(BaseModel):
    """Supervisor's structured plan for an investigation"""
    investigation_id: UUID
    tasks: List[AgentTask]
    plan_rationale: str = Field(..., description="Why Supervisor chose these agents in this order")
    estimated_duration_sec: int = Field(..., ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "investigation_id": "123e4567-e89b-12d3-a456-426614174000",
                "tasks": [],
                "plan_rationale": "Circular trading investigation requires: (1) Financial analysis for cash flow divergence, (2) Graph analysis for transaction loops, (3) Compliance check for SEBI violations",
                "estimated_duration_sec": 1800
            }
        }
    )


class InvestigationState(BaseModel):
    """Checkpointed state of an investigation (saved to Supabase)"""
    id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    agent_type: AgentType
    status: AgentStatus
    findings: List[Finding]
    confidence: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # For Supabase ORM compatibility (allows reading from objects, not just dicts)
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# API CONTRACTS
# ==========================================

class InvestigationRequest(BaseModel):
    """Client request to start a new investigation"""
    query: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Natural language investigation query"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional context like uploaded file keys, date ranges, etc."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Investigate Adani for circular trading in Q3 2024",
                "context": {
                    "focus_period": "Q3-2024",
                    "include_subsidiaries": True
                }
            }
        }
    )


class InvestigationResponse(BaseModel):
    """Response when investigation is successfully queued"""
    investigation_id: UUID
    status: InvestigationStatus
    stream_url: str = Field(..., description="SSE endpoint URL for live updates")
    estimated_completion_time: Optional[datetime] = None


class DomainFindings(BaseModel):
    """Findings from a single domain (Financial, Graph, Audio, Compliance)"""
    agent_type: AgentType
    findings: List[Finding]
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: AgentStatus


class InvestigationReport(BaseModel):
    """Final investigation report returned to client"""
    investigation_id: UUID
    query: str
    status: InvestigationStatus
    fraud_risk_score: float = Field(..., ge=0.0, le=10.0, description="0 = safe, 10 = critical fraud")
    verdict: Verdict
    summary: str = Field(..., description="Executive summary of the investigation")
    domains: Dict[AgentType, DomainFindings]
    cross_domain_insights: List[str] = Field(
        default_factory=list,
        description="Insights that connect findings across multiple domains"
    )
    evidence_chain: List[str] = Field(
        default_factory=list,
        description="Step-by-step evidence trail showing how conclusions were reached"
    )
    audit_trail_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        # Pydantic V2 serializes datetimes to ISO 8601 by default
        json_schema_extra={
            "example": {
                "investigation_id": "123e4567-e89b-12d3-a456-426614174000",
                "query": "Investigate Adani for circular trading",
                "status": "completed",
                "fraud_risk_score": 9.2,
                "verdict": "critical",
                "summary": "High probability of circular trading fraud. Financial, Graph, and Compliance domains all flagged the same ₹500Cr transaction loop.",
                "domains": {},
                "cross_domain_insights": [
                    "₹500Cr undisclosed transaction (Financial) matches exact loop amount (Graph)",
                    "CEO stress spike (Audio) occurred when questioned about this transaction"
                ],
                "evidence_chain": [
                    "Q3 2024 filing shows ₹500Cr transaction with Shell A",
                    "Graph analysis reveals Shell A → Shell B → Adani loop",
                    "SEBI LODR Regulation 23 requires disclosure of related-party transactions > ₹1Cr",
                    "Transaction was NOT disclosed → violation confirmed"
                ],
                "audit_trail_id": "audit_xyz789",
                "created_at": "2024-02-04T10:30:00Z",
                "updated_at": "2024-02-04T12:00:00Z"
            }
        }
    )


# ==========================================
# AUDIT TRAIL
# ==========================================

class AuditLogEntry(BaseModel):
    """Single entry in the audit trail"""
    id: Optional[int] = None
    investigation_id: UUID
    step_type: str = Field(..., description="'plan', 'agent_start', 'agent_end', 'reflection', 'synthesis'")
    agent_type: Optional[AgentType] = None
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    output_payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# SSE EVENTS
# ==========================================

class SSEEvent(BaseModel):
    """Server-Sent Event for real-time updates"""
    event: str  # Event type (e.g., 'agent_started', 'agent_completed', 'investigation_complete')
    data: Dict[str, Any]

    def to_sse_format(self) -> str:
        """Convert to SSE wire format"""
        import json
        return f"event: {self.event}\ndata: {json.dumps(self.data)}\n\n"
