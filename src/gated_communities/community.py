"""Community model and configuration."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CommunityVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    HIDDEN = "hidden"


@dataclass
class CommunityConfig:
    """Configuration for a gated community."""

    name: str
    description: str = ""
    visibility: CommunityVisibility = CommunityVisibility.PRIVATE
    require_approval: bool = True
    max_members: int | None = None
    invite_only: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Community:
    """A gated community with access control."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config: CommunityConfig = field(default_factory=lambda: CommunityConfig(name=""))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    member_count: int = 0
    is_active: bool = True

    def can_join(self, user_id: str) -> bool:
        """Check if a user can join this community."""
        if not self.is_active:
            return False
        if self.config.max_members and self.member_count >= self.config.max_members:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.config.name,
            "description": self.config.description,
            "visibility": self.config.visibility.value,
            "require_approval": self.config.require_approval,
            "max_members": self.config.max_members,
            "invite_only": self.config.invite_only,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "member_count": self.member_count,
            "is_active": self.is_active,
        }
