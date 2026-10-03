"""Pydantic schemas for gated-communities API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Community
# ---------------------------------------------------------------------------


class CommunityCreate(BaseModel):
    """Schema for creating a new community."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=2000)
    is_private: bool = False
    tags: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def tags_unique(cls, v: list[str]) -> list[str]:
        seen: set[str] = set()
        for tag in v:
            lowered = tag.lower()
            if lowered in seen:
                raise ValueError(f"duplicate tag: {tag}")
            seen.add(lowered)
        return v


class CommunityUpdate(BaseModel):
    """Schema for updating an existing community."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, min_length=1, max_length=2000)
    is_private: bool | None = None
    tags: list[str] | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("name must not be blank")
        return v.strip() if v is not None else v


class CommunityResponse(BaseModel):
    """Schema for community response payloads."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    is_private: bool
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    member_count: int = 0


# ---------------------------------------------------------------------------
# Member
# ---------------------------------------------------------------------------


class MemberCreate(BaseModel):
    """Schema for adding a member to a community."""

    user_id: int = Field(..., gt=0)
    role: str = Field(default="member", pattern="^(member|moderator|admin)$")

    @field_validator("role")
    @classmethod
    def role_valid(cls, v: str) -> str:
        allowed = {"member", "moderator", "admin"}
        if v not in allowed:
            raise ValueError(f"role must be one of {allowed}")
        return v


class MemberUpdate(BaseModel):
    """Schema for updating a member's role or status."""

    role: str | None = Field(None, pattern="^(member|moderator|admin)$")
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def role_valid(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"member", "moderator", "admin"}
        if v not in allowed:
            raise ValueError(f"role must be one of {allowed}")
        return v


class MemberResponse(BaseModel):
    """Schema for member response payloads."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    community_id: int
    user_id: int
    role: str
    is_active: bool
    joined_at: datetime


# ---------------------------------------------------------------------------
# Post
# ---------------------------------------------------------------------------


class PostCreate(BaseModel):
    """Schema for creating a new post."""

    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=1, max_length=50_000)
    is_pinned: bool = False

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v.strip()


class PostUpdate(BaseModel):
    """Schema for updating an existing post."""

    title: str | None = Field(None, min_length=1, max_length=300)
    content: str | None = Field(None, min_length=1, max_length=50_000)
    is_pinned: bool | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("title must not be blank")
        return v.strip() if v is not None else v


class PostResponse(BaseModel):
    """Schema for post response payloads."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    community_id: int
    author_id: int
    title: str
    content: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    comment_count: int = 0


# ---------------------------------------------------------------------------
# Comment
# ---------------------------------------------------------------------------


class CommentCreate(BaseModel):
    """Schema for creating a new comment."""

    content: str = Field(..., min_length=1, max_length=10_000)
    parent_id: int | None = Field(None, gt=0)

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be blank")
        return v.strip()


class CommentUpdate(BaseModel):
    """Schema for updating an existing comment."""

    content: str | None = Field(None, min_length=1, max_length=10_000)

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("content must not be blank")
        return v.strip() if v is not None else v


class CommentResponse(BaseModel):
    """Schema for comment response payloads."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    author_id: int
    content: str
    parent_id: int | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------


class EventCreate(BaseModel):
    """Schema for creating a new event."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5_000)
    location: str | None = Field(None, max_length=300)
    starts_at: datetime
    ends_at: datetime

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v.strip()

    @field_validator("ends_at")
    @classmethod
    def ends_after_start(cls, v: datetime, info) -> datetime:
        if "starts_at" in info.data and v <= info.data["starts_at"]:
            raise ValueError("ends_at must be after starts_at")
        return v


class EventUpdate(BaseModel):
    """Schema for updating an existing event."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1, max_length=5_000)
    location: str | None = Field(None, max_length=300)
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("title must not be blank")
        return v.strip() if v is not None else v

    @field_validator("ends_at")
    @classmethod
    def ends_after_start(cls, v: datetime | None, info) -> datetime | None:
        if v is None:
            return v
        if "starts_at" in info.data and info.data["starts_at"] is not None:
            if v <= info.data["starts_at"]:
                raise ValueError("ends_at must be after starts_at")
        return v


class EventResponse(BaseModel):
    """Schema for event response payloads."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    community_id: int
    title: str
    description: str
    location: str | None = None
    starts_at: datetime
    ends_at: datetime
    created_at: datetime
    updated_at: datetime
    attendee_count: int = 0
