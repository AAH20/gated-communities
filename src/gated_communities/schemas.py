"""Pydantic schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CommunityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    is_private: bool = False
    tier_id: str = "free"
    capacity: int = Field(default=100, ge=1, le=100000)


class CommunityResponse(BaseModel):
    id: int
    name: str
    description: str
    is_private: bool
    tier_id: str
    capacity: int
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class MemberCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    role: str = "member"
    community_id: int


class MemberResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    community_id: int
    is_active: bool
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ModerationItemCreate(BaseModel):
    type: str = Field(..., min_length=1, max_length=50)
    author: str = Field(..., min_length=1, max_length=255)
    reason: str = ""


class ModerationItemResponse(BaseModel):
    id: int
    type: str
    author: str
    reason: str
    status: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class AuditLogCreate(BaseModel):
    user_id: str | None = None
    action: str = Field(..., min_length=1, max_length=100)
    resource_type: str | None = None
    resource_id: str | None = None
    details: str = ""


class AuditLogResponse(BaseModel):
    id: int
    user_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    details: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class BulkMemberUpdate(BaseModel):
    member_ids: list[int] = Field(..., min_length=1)
    action: str = Field(..., pattern="^(add|remove|update)$")
    role: str | None = None


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str


class LiveResponse(BaseModel):
    status: str
