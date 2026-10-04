"""Moderation models."""

from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ModerationStatus(StrEnum):
    """Moderation status."""
    PENDING = "pending"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ModerationPriority(StrEnum):
    """Moderation priority."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModerationItem(BaseModel):
    """Moderation item model."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    community_id: str = Field(..., min_length=1)
    reporter_id: str = Field(..., min_length=1)
    target_type: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    description: str = Field(default="")
    status: ModerationStatus = ModerationStatus.PENDING
    priority: ModerationPriority = ModerationPriority.MEDIUM
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_notes: str | None = None
    action_taken: str | None = None
