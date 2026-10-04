"""Events module."""

from __future__ import annotations
from enum import StrEnum
from typing import Any, Callable


class CommunityEventType(StrEnum):
    """Community event type."""
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    POST_CREATED = "post_created"
    COMMUNITY_CREATED = "community_created"


class CommunityEvent:
    """Community event."""
    def __init__(self, event_type: CommunityEventType, data: dict[str, Any] | None = None):
        self.event_type = event_type
        self.data = data or {}


class EventBus:
    """Event bus."""
    def __init__(self):
        self._handlers: dict[CommunityEventType, list[Callable]] = {}

    def subscribe(self, event_type: CommunityEventType, handler: Callable):
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: CommunityEvent):
        for handler in self._handlers.get(event.event_type, []):
            handler(event)
