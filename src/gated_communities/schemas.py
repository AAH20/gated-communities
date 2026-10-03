"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


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
    created_at: Optional[datetime] = None

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
    created_at: Optional[datetime] = None

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
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogCreate(BaseModel):
    user_id: Optional[str] = None
    action: str = Field(..., min_length=1, max_length=100)
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: str = ""


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BulkMemberUpdate(BaseModel):
    member_ids: List[int] = Field(..., min_length=1)
    action: str = Field(..., pattern="^(add|remove|update)$")
    role: Optional[str] = None


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str


class LiveResponse(BaseModel):
    status: str
