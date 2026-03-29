from sqlmodel import Column, Integer, String, DateTime, Text, Field, SQLModel, Float
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional


class FinancialFilingBase(SQLModel):
    symbol: str
    filing_type: str
    period: str
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    filing_data: Optional[str] = None  # JSON string


class FinancialFiling(FinancialFilingBase, table=True):
    __tablename__ = "financial_filings"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=func.now)


class NewsArticleBase(SQLModel):
    title: str
    content: str
    source: str
    url: str
    published_at: datetime
    sentiment_score: Optional[float] = None
    relevance_score: Optional[float] = None


class NewsArticle(NewsArticleBase, table=True):
    __tablename__ = "news_articles"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=func.now)


class ComplianceRecordBase(SQLModel):
    entity: str
    violation_type: str
    description: str
    severity: str
    date: datetime
    fine_amount: Optional[float] = None
    status: str = "active"
    details: Optional[str] = None  # JSON string


class ComplianceRecord(ComplianceRecordBase, table=True):
    __tablename__ = "compliance_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=func.now)


class AudioTranscriptBase(SQLModel):
    title: str
    content: str
    speaker: str
    company: str
    date: datetime
    duration_seconds: Optional[int] = None
    sentiment_score: Optional[float] = None


class AudioTranscript(AudioTranscriptBase, table=True):
    __tablename__ = "audio_transcripts"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=func.now)
