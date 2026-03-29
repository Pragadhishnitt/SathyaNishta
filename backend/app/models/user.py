from sqlmodel import Column, Integer, String, Boolean, DateTime, Text, Field, SQLModel
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional


class UserBase(SQLModel):
    email: str = Field(index=True, unique=True)
    name: str
    company: Optional[str] = None
    role: Optional[str] = None
    bio: Optional[str] = None


class User(UserBase, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: Optional[str] = None  # Nullable for OAuth users
    is_active: bool = True
    is_verified: bool = False
    is_premium: bool = False

    # OAuth provider info
    provider: Optional[str] = None  # 'google', 'github', etc.
    provider_id: Optional[str] = None

    # Email verification
    verification_token: Optional[str] = None
    verification_expires: Optional[datetime] = None

    # Password reset
    reset_token: Optional[str] = None
    reset_expires: Optional[datetime] = None

    # Timestamps
    created_at: datetime = Field(default_factory=func.now)
    updated_at: datetime = Field(default_factory=func.now, sa_column_kwargs={"onupdate": func.now()})
    last_login: Optional[datetime] = None


class UserPublic(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    is_premium: bool
    provider: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
