"""Moderation module."""

from __future__ import annotations
from enum import StrEnum
from typing import Any


class ModerationStatus(StrEnum):
    """Moderation status."""
    PENDING = "pending"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ModerationAction(StrEnum):
    """Moderation action."""
    WARN = "warn"
    BAN = "ban"
    DISMISS = "dismiss"
    DELETE = "delete"


class ModerationItem:
    """Moderation item."""
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", "")
        self.community_id = kwargs.get("community_id", "")
        self.reporter_id = kwargs.get("reporter_id", "")
        self.reason = kwargs.get("reason", "")
        self.status = kwargs.get("status", ModerationStatus.PENDING)
        self.priority = kwargs.get("priority", "medium")
        self.description = kwargs.get("description", "")


class ModerationQueue:
    """Moderation queue."""
    def __init__(self):
        self._items: list[ModerationItem] = []

    def add(self, item: ModerationItem):
        self._items.append(item)

    def get_pending(self) -> list[ModerationItem]:
        return [i for i in self._items if i.status == ModerationStatus.PENDING]


class ModerationAnalytics:
    """Moderation analytics."""
    def __init__(self):
        self._data: dict[str, Any] = {}


class ModerationService:
    """Moderation service."""
    def __init__(self):
        self.queue = ModerationQueue()
        self.analytics = ModerationAnalytics()
