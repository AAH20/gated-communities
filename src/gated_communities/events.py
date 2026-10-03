"""Event system for community activities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class CommunityEventType(str, Enum):
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    MEMBER_SUSPENDED = "member_suspended"
    MEMBER_BANNED = "member_banned"
    ACCESS_REQUESTED = "access_requested"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    GATE_ADDED = "gate_added"
    GATE_REMOVED = "gate_removed"
    COMMUNITY_CREATED = "community_created"
    COMMUNITY_UPDATED = "community_updated"


@dataclass
class CommunityEvent:
    """An event in the community system."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: CommunityEventType = CommunityEventType.COMMUNITY_CREATED
    community_id: str = ""
    user_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class EventBus:
    """Simple event bus for community events."""

    def __init__(self) -> None:
        self._handlers: dict[CommunityEventType, list[Callable]] = {}
        self._history: list[CommunityEvent] = []

    def subscribe(
        self,
        event_type: CommunityEventType,
        handler: Callable[[CommunityEvent], None],
    ) -> None:
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(
        self,
        event_type: CommunityEventType,
        handler: Callable[[CommunityEvent], None],
    ) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    def publish(self, event: CommunityEvent) -> None:
        """Publish an event."""
        self._history.append(event)
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            handler(event)

    def get_history(
        self,
        community_id: str | None = None,
        event_type: CommunityEventType | None = None,
    ) -> list[CommunityEvent]:
        """Get event history with optional filtering."""
        events = self._history
        if community_id:
            events = [e for e in events if e.community_id == community_id]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events
