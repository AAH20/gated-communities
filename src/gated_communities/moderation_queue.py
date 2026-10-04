"""Moderation queue module."""

from __future__ import annotations
from typing import Any


class ModerationQueueError(Exception):
    """Moderation queue error."""
    pass


class QueueItemNotFoundError(ModerationQueueError):
    """Queue item not found error."""
    pass


class QueueItemAlreadyProcessedError(ModerationQueueError):
    """Queue item already processed error."""
    pass


_queue: list[dict[str, Any]] = []


def add_to_queue(item: dict[str, Any]) -> dict[str, Any]:
    """Add item to queue."""
    _queue.append(item)
    return item


def get_queue_status() -> dict[str, Any]:
    """Get queue status."""
    return {"total": len(_queue), "pending": len(_queue)}


def process_queue_item(item_id: str) -> dict[str, Any]:
    """Process queue item."""
    for item in _queue:
        if item.get("id") == item_id:
            return item
    raise QueueItemNotFoundError(f"Item {item_id} not found")
