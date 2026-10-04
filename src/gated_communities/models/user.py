"""User models."""

from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """User model."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    username: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=1)
    hashed_password: str = Field(default="")
    is_active: bool = True
    is_moderator: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
