"""Community module."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class CommunityVisibility(StrEnum):
    """Community visibility."""
    PUBLIC = "public"
    PRIVATE = "private"
    SECRET = "secret"


@dataclass
class CommunityConfig:
    """Community configuration."""
    visibility: CommunityVisibility = CommunityVisibility.PUBLIC
    max_members: int = 100
    allow_invites: bool = True


@dataclass
class Community:
    """Community model."""
    id: str = ""
    name: str = ""
    description: str = ""
    config: CommunityConfig = field(default_factory=CommunityConfig)
    members: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
