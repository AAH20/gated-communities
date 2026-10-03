"""Moderation Queue Agent for Gated Communities.

Provides queue status metrics and prioritization logic for community
moderation workflows.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class Priority(Enum):
    """Priority levels for moderation queue items."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReportReason(Enum):
    """Reasons a piece of content may be reported."""

    SPAM = "spam"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    MISINFORMATION = "misinformation"
    NSFW = "nsfw"
    IMPERSONATION = "impersonation"
    OTHER = "other"


@dataclass
class QueueItem:
    """A single item in the moderation queue."""

    item_id: str
    community_id: str
    reporter_id: str
    content_id: str
    reason: ReportReason
    priority: Priority
    created_at: str  # ISO 8601 timestamp
    report_count: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class QueueMetrics:
    """Aggregate metrics for the moderation queue."""

    total_items: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    avg_resolution_time_hours: float
    oldest_item_age_hours: float
    items_by_reason: dict[str, int]
    items_by_community: dict[str, int]


# ── Mock Data ────────────────────────────────────────────────────────────────

_MOCK_QUEUE_ITEMS: list[QueueItem] = [
    QueueItem(
        item_id="q-001",
        community_id="comm-alpha",
        reporter_id="user-101",
        content_id="post-5001",
        reason=ReportReason.HATE_SPEECH,
        priority=Priority.CRITICAL,
        created_at="2026-10-03T08:15:00Z",
        report_count=12,
        metadata={"auto_flagged": True, "confidence": 0.94},
    ),
    QueueItem(
        item_id="q-002",
        community_id="comm-beta",
        reporter_id="user-202",
        content_id="post-5002",
        reason=ReportReason.HARASSMENT,
        priority=Priority.HIGH,
        created_at="2026-10-03T09:30:00Z",
        report_count=5,
        metadata={"auto_flagged": False},
    ),
    QueueItem(
        item_id="q-003",
        community_id="comm-alpha",
        reporter_id="user-103",
        content_id="post-5003",
        reason=ReportReason.SPAM,
        priority=Priority.MEDIUM,
        created_at="2026-10-03T10:00:00Z",
        report_count=3,
        metadata={"auto_flagged": True, "confidence": 0.78},
    ),
    QueueItem(
        item_id="q-004",
        community_id="comm-gamma",
        reporter_id="user-301",
        content_id="post-5004",
        reason=ReportReason.MISINFORMATION,
        priority=Priority.HIGH,
        created_at="2026-10-03T10:45:00Z",
        report_count=7,
        metadata={"auto_flagged": False},
    ),
    QueueItem(
        item_id="q-005",
        community_id="comm-beta",
        reporter_id="user-205",
        content_id="post-5005",
        reason=ReportReason.NSFW,
        priority=Priority.CRITICAL,
        created_at="2026-10-03T11:00:00Z",
        report_count=9,
        metadata={"auto_flagged": True, "confidence": 0.91},
    ),
    QueueItem(
        item_id="q-006",
        community_id="comm-alpha",
        reporter_id="user-106",
        content_id="post-5006",
        reason=ReportReason.OTHER,
        priority=Priority.LOW,
        created_at="2026-10-03T11:30:00Z",
        report_count=1,
        metadata={"auto_flagged": False},
    ),
    QueueItem(
        item_id="q-007",
        community_id="comm-gamma",
        reporter_id="user-307",
        content_id="post-5007",
        reason=ReportReason.IMPERSONATION,
        priority=Priority.HIGH,
        created_at="2026-10-03T12:00:00Z",
        report_count=4,
        metadata={"auto_flagged": False},
    ),
    QueueItem(
        item_id="q-008",
        community_id="comm-beta",
        reporter_id="user-208",
        content_id="post-5008",
        reason=ReportReason.SPAM,
        priority=Priority.LOW,
        created_at="2026-10-03T12:30:00Z",
        report_count=2,
        metadata={"auto_flagged": True, "confidence": 0.65},
    ),
]


# ── In-memory store for dynamic queue operations ─────────────────────────────

_queue_store: dict[str, dict[str, Any]] = {}


# ── Public API ───────────────────────────────────────────────────────────────


def get_queue_status() -> QueueMetrics:
    """Return current moderation queue metrics.

    Computes aggregate statistics from the mock queue data including
    counts by priority, average resolution time, and distribution
    across reasons and communities.

    Returns:
        QueueMetrics with all aggregate queue statistics.
    """
    total = len(_MOCK_QUEUE_ITEMS)

    critical_count = sum(1 for i in _MOCK_QUEUE_ITEMS if i.priority == Priority.CRITICAL)
    high_count = sum(1 for i in _MOCK_QUEUE_ITEMS if i.priority == Priority.HIGH)
    medium_count = sum(1 for i in _MOCK_QUEUE_ITEMS if i.priority == Priority.MEDIUM)
    low_count = sum(1 for i in _MOCK_QUEUE_ITEMS if i.priority == Priority.LOW)

    # Mock resolution times (hours) per item
    resolution_times = [2.5, 4.0, 8.0, 3.5, 1.5, 24.0, 5.0, 12.0]
    avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0.0

    # Mock oldest item age
    oldest_age = 26.0

    # Count by reason
    items_by_reason: dict[str, int] = {}
    for item in _MOCK_QUEUE_ITEMS:
        key = item.reason.value
        items_by_reason[key] = items_by_reason.get(key, 0) + 1

    # Count by community
    items_by_community: dict[str, int] = {}
    for item in _MOCK_QUEUE_ITEMS:
        items_by_community[item.community_id] = items_by_community.get(item.community_id, 0) + 1

    return QueueMetrics(
        total_items=total,
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        avg_resolution_time_hours=avg_resolution,
        oldest_item_age_hours=oldest_age,
        items_by_reason=items_by_reason,
        items_by_community=items_by_community,
    )


def prioritize_queue() -> list[QueueItem]:
    """Return the moderation queue sorted by priority (highest first).

    Items are sorted first by priority level (CRITICAL → HIGH → MEDIUM → LOW),
    then by report count (descending), and finally by creation time (oldest first).

    Returns:
        List of QueueItem sorted by priority.
    """
    priority_order = {
        Priority.CRITICAL: 0,
        Priority.HIGH: 1,
        Priority.MEDIUM: 2,
        Priority.LOW: 3,
    }

    return sorted(
        _MOCK_QUEUE_ITEMS,
        key=lambda item: (
            priority_order[item.priority],
            -item.report_count,
            item.created_at,
        ),
    )


def add_to_queue(content_id: str, reason: str) -> dict:
    """Add content to the moderation queue.

    Args:
        content_id: Unique identifier for the content to be moderated.
        reason: Reason for adding the content to the moderation queue.

    Returns:
        A dictionary containing the queue item details including
        the generated queue_id, content_id, reason, status, and timestamps.

    Raises:
        ValueError: If content_id or reason is empty or None.
    """
    if not content_id or not isinstance(content_id, str):
        raise ValueError("content_id must be a non-empty string")
    if not reason or not isinstance(reason, str):
        raise ValueError("reason must be a non-empty string")

    queue_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    queue_item = {
        "queue_id": queue_id,
        "content_id": content_id,
        "reason": reason,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "decision": None,
        "decided_at": None,
    }

    _queue_store[queue_id] = queue_item
    return queue_item


def get_queue_status(queue_id: str) -> dict:
    """Get the current status of a moderation queue item.

    Args:
        queue_id: Unique identifier for the queue item.

    Returns:
        A dictionary containing the queue item's current status and details.

    Raises:
        ValueError: If queue_id is empty or None.
        KeyError: If the queue_id does not exist in the store.
    """
    if not queue_id or not isinstance(queue_id, str):
        raise ValueError("queue_id must be a non-empty string")

    if queue_id not in _queue_store:
        raise KeyError(f"Queue item with id '{queue_id}' not found")

    return dict(_queue_store[queue_id])


def process_queue_item(queue_id: str, decision: str) -> bool:
    """Process a moderation queue item with a decision.

    Args:
        queue_id: Unique identifier for the queue item to process.
        decision: The moderation decision (e.g., 'approve', 'reject', 'escalate').

    Returns:
        True if the queue item was successfully processed.

    Raises:
        ValueError: If queue_id or decision is empty or None, or if the
            queue item has already been processed.
        KeyError: If the queue_id does not exist in the store.
    """
    if not queue_id or not isinstance(queue_id, str):
        raise ValueError("queue_id must be a non-empty string")
    if not decision or not isinstance(decision, str):
        raise ValueError("decision must be a non-empty string")

    if queue_id not in _queue_store:
        raise KeyError(f"Queue item with id '{queue_id}' not found")

    queue_item = _queue_store[queue_id]

    if queue_item["status"] != "pending":
        raise ValueError(
            f"Queue item '{queue_id}' has already been processed "
            f"with decision '{queue_item['decision']}'"
        )

    now = datetime.now(UTC).isoformat()
    queue_item["status"] = "processed"
    queue_item["decision"] = decision
    queue_item["decided_at"] = now
    queue_item["updated_at"] = now

    return True
