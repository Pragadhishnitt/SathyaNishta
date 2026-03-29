from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

# Import Enums from contracts (we assume we can import from there, or redefine)
# Ideally, we should move the contracts enums to a shared place, but for now
# we will redefine them to ensure standalone functionality or import if available.
# Given the restrictions, I'll redefine the relevant Enums using SQLModel's Enum support if needed,
# or just use strings for simplicity in the DB layer, validated by Pydantic.
# Using strings for Enums in DB is often safer for migrations.


class Investigation(SQLModel, table=True):
    """Database model for an investigation"""

    __tablename__ = "investigations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    query: str = Field(index=True)
    status: str = Field(default="queued", index=True)  # Queued, Running, Completed, Failed
    fraud_risk_score: Optional[float] = Field(default=None)
    verdict: Optional[str] = Field(default=None)  # Critical, High, Medium, Low, Safe
    summary: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

    # Store complex objects as JSON
    domains: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    cross_domain_insights: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    evidence_chain: List[str] = Field(default_factory=list, sa_column=Column(JSON))


class AuditLog(SQLModel, table=True):
    """Database model for audit steps"""

    __tablename__ = "audit_trails"

    id: Optional[int] = Field(default=None, primary_key=True)
    investigation_id: UUID = Field(foreign_key="investigations.id", index=True)
    step_type: str  # plan, agent_start, agent_end, reflection, synthesis
    agent_type: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Payload storage
    input_payload: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    output_payload: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    model_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    model_config = {"protected_namespaces": ()}
