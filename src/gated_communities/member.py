"""Member module."""

from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum


class MemberRole(StrEnum):
    """Member role."""
    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"


class MemberStatus(StrEnum):
    """Member status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


@dataclass
class Member:
    """Member model."""
    id: str = ""
    name: str = ""
    email: str = ""
    status: MemberStatus = MemberStatus.ACTIVE
    role: MemberRole = MemberRole.MEMBER
    community_id: str = ""
    access_level: str = "none"
