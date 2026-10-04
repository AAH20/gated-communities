"""Invitation models."""

from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class InvitationStatus(StrEnum):
    """Invitation status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class Invitation(BaseModel):
    """Invitation model."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    community_id: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    status: InvitationStatus = InvitationStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None


class InvitationCreate(BaseModel):
    """Create invitation request."""
    community_id: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)


class InvitationUpdate(BaseModel):
    """Update invitation request."""
    status: InvitationStatus | None = None
