"""Member model and roles."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MemberRole(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"
    GUEST = "guest"


class MemberStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"
    REMOVED = "removed"


@dataclass
class Member:
    """A community member."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    community_id: str = ""
    role: MemberRole = MemberRole.MEMBER
    status: MemberStatus = MemberStatus.PENDING
    joined_at: datetime = field(default_factory=datetime.utcnow)
    invited_by: str | None = None
    metadata: dict = field(default_factory=dict)

    def can_moderate(self) -> bool:
        """Check if member can moderate content."""
        return self.role in (MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MODERATOR)

    def can_invite(self) -> bool:
        """Check if member can invite others."""
        return self.role in (MemberRole.OWNER, MemberRole.ADMIN)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "community_id": self.community_id,
            "role": self.role.value,
            "status": self.status.value,
            "joined_at": self.joined_at.isoformat(),
            "invited_by": self.invited_by,
        }
