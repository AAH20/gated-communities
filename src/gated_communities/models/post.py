"""Post models."""

from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class PostStatus(StrEnum):
    """Post status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Post(BaseModel):
    """Post model."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    community_id: str = Field(..., min_length=1)
    author_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    status: PostStatus = PostStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
