import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.sql import func
from sqlmodel import Column, DateTime, Field, ForeignKey, Integer, SQLModel, String, Text


class ChatThreadBase(SQLModel):
    title: str
    mode: str = Field(default="standard")  # "standard" or "sathyanishta"
    investigation_id: Optional[str] = None


class ChatThread(ChatThreadBase, table=True):
    __tablename__ = "chat_threads"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=func.now)
    updated_at: datetime = Field(default_factory=func.now, sa_column_kwargs={"onupdate": func.now()})


class ChatMessageBase(SQLModel):
    content: str
    role: str  # "user" or "assistant"
    extra_data: Optional[str] = None  # JSON string for additional data


class ChatMessage(ChatMessageBase, table=True):
    __tablename__ = "chat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    thread_id: str = Field(foreign_key="chat_threads.id")
    created_at: datetime = Field(default_factory=func.now)

    # Relationships
    user_id: int = Field(foreign_key="users.id")


class ChatThreadWithMessages(ChatThreadBase):
    id: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessage] = []
