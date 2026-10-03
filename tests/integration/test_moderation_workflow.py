"""
Integration tests for the moderation workflow in gated-communities.

Tests cover:
1. Full moderation lifecycle (create → resolve → delete)
2. Moderation queue flow (add → process → status)
3. Moderation analytics flow (create items → metrics → anomaly flagging)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.gated_communities.moderation import (
    ModerationItem,
    ModerationQueue,
    ModerationAnalytics,
    ModerationStatus,
    ModerationAction,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def moderation_service():
    """Provide a fresh moderation service instance."""
    from src.gated_communities.moderation import ModerationService

    return ModerationService()


@pytest.fixture
def sample_item():
    """Provide a sample moderation item."""
    return ModerationItem(
        id="item-001",
        community_id="community-001",
        content_id="content-001",
        content_type="post",
        author_id="user-001",
        reason="spam",
        status=ModerationStatus.PENDING,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def moderation_queue():
    """Provide a fresh moderation queue."""
    return ModerationQueue()


@pytest.fixture
def analytics():
    """Provide a fresh moderation analytics instance."""
    return ModerationAnalytics()


# ---------------------------------------------------------------------------
# Test 1: Full moderation lifecycle
# ---------------------------------------------------------------------------


class TestFullModerationLifecycle:
    """Test the complete lifecycle of a moderation item."""

    def test_full_moderation_lifecycle(self, moderation_service, sample_item):
        """Create item → resolve → delete."""
        # Step 1: Create item
        created = moderation_service.create_item(sample_item)
        assert created.id == "item-001"
        assert created.status == ModerationStatus.PENDING
        assert created.community_id == "community-001"

        # Verify item is retrievable
        retrieved = moderation_service.get_item("item-001")
        assert retrieved is not None
        assert retrieved.id == "item-001"
        assert retrieved.status == ModerationStatus.PENDING

        # Step 2: Resolve item
        resolved = moderation_service.resolve_item(
            item_id="item-001",
            action=ModerationAction.APPROVE,
            moderator_id="mod-001",
            notes="Content reviewed and approved",
        )
        assert resolved.status == ModerationStatus.RESOLVED
        assert resolved.resolved_by == "mod-001"
        assert resolved.resolution_notes == "Content reviewed and approved"
        assert resolved.resolved_at is not None

        # Verify resolution persisted
        retrieved_after = moderation_service.get_item("item-001")
        assert retrieved_after.status == ModerationStatus.RESOLVED

        # Step 3: Delete item
        deleted = moderation_service.delete_item("item-001")
        assert deleted is True

        # Verify item no longer exists
        gone = moderation_service.get_item("item-001")
        assert gone is None

    def test_full_moderation_lifecycle_with_rejection(self, moderation_service):
        """Create item → reject → delete."""
        item = ModerationItem(
            id="item-reject-001",
            community_id="community-002",
            content_id="content-002",
            content_type="comment",
            author_id="user-002",
            reason="harassment",
            status=ModerationStatus.PENDING,
            created_at=datetime.utcnow(),
        )

        created = moderation_service.create_item(item)
        assert created.status == ModerationStatus.PENDING

        resolved = moderation_service.resolve_item(
            item_id="item-reject-001",
            action=ModerationAction.REJECT,
            moderator_id="mod-002",
            notes="Violates community guidelines",
        )
        assert resolved.status == ModerationStatus.RESOLVED
        assert resolved.resolution_action == ModerationAction.REJECT

        deleted = moderation_service.delete_item("item-reject-001")
        assert deleted is True


# ---------------------------------------------------------------------------
# Test 2: Moderation queue flow
# ---------------------------------------------------------------------------


class TestModerationQueueFlow:
    """Test the moderation queue add → process → status flow."""

    def test_moderation_queue_flow(self, moderation_queue, sample_item):
        """Add to queue → process → get status."""
        # Step 1: Add item to queue
        moderation_queue.enqueue(sample_item)
        assert moderation_queue.size() == 1
        assert not moderation_queue.is_empty()

        # Step 2: Process item from queue
        processed = moderation_queue.process_next()
        assert processed is not None
        assert processed.id == "item-001"
        assert processed.status == ModerationStatus.IN_REVIEW

        # Step 3: Get queue status
        status = moderation_queue.get_status()
        assert status["pending"] == 0
        assert status["in_review"] == 1
        assert status["total"] == 1

    def test_moderation_queue_flow_multiple_items(self, moderation_queue):
        """Add multiple items → process all → verify empty."""
        items = [
            ModerationItem(
                id=f"queue-item-{i}",
                community_id="community-001",
                content_id=f"content-{i}",
                content_type="post",
                author_id=f"user-{i}",
                reason="spam",
                status=ModerationStatus.PENDING,
                created_at=datetime.utcnow(),
            )
            for i in range(3)
        ]

        # Enqueue all items
        for item in items:
            moderation_queue.enqueue(item)
        assert moderation_queue.size() == 3

        # Process all items
        processed_items = []
        while not moderation_queue.is_empty():
            processed = moderation_queue.process_next()
            processed_items.append(processed)

        assert len(processed_items) == 3
        assert moderation_queue.is_empty()

        # Verify final status
        status = moderation_queue.get_status()
        assert status["pending"] == 0
        assert status["in_review"] == 3
        assert status["total"] == 3

    def test_moderation_queue_peek(self, moderation_queue, sample_item):
        """Verify peek returns item without removing it."""
        moderation_queue.enqueue(sample_item)

        peeked = moderation_queue.peek()
        assert peeked.id == "item-001"
        assert moderation_queue.size() == 1  # Still in queue


# ---------------------------------------------------------------------------
# Test 3: Moderation analytics flow
# ---------------------------------------------------------------------------


class TestModerationAnalyticsFlow:
    """Test the moderation analytics create → metrics → anomaly flow."""

    def test_moderation_analytics_flow(self, moderation_service, analytics):
        """Create items → get metrics → flag anomaly."""
        # Step 1: Create multiple items
        items = []
        for i in range(5):
            item = ModerationItem(
                id=f"analytics-item-{i}",
                community_id="community-analytics",
                content_id=f"content-analytics-{i}",
                content_type="post",
                author_id=f"user-analytics-{i}",
                reason="spam" if i < 3 else "harassment",
                status=ModerationStatus.PENDING,
                created_at=datetime.utcnow() - timedelta(hours=i),
            )
            created = moderation_service.create_item(item)
            items.append(created)

        assert len(items) == 5

        # Step 2: Get metrics
        metrics = analytics.get_metrics(community_id="community-analytics")
        assert metrics["total_items"] == 5
        assert metrics["pending_count"] == 5
        assert metrics["resolved_count"] == 0
        assert "spam" in metrics["reason_breakdown"]
        assert "harassment" in metrics["reason_breakdown"]
        assert metrics["reason_breakdown"]["spam"] == 3
        assert metrics["reason_breakdown"]["harassment"] == 2

        # Step 3: Flag anomaly (unusual spike in items)
        # Create a burst of items to trigger anomaly detection
        for i in range(20):
            burst_item = ModerationItem(
                id=f"burst-item-{i}",
                community_id="community-analytics",
                content_id=f"burst-content-{i}",
                content_type="post",
                author_id=f"burst-user-{i}",
                reason="spam",
                status=ModerationStatus.PENDING,
                created_at=datetime.utcnow(),
            )
            moderation_service.create_item(burst_item)

        # Check for anomalies
        anomalies = analytics.detect_anomalies(community_id="community-analytics")
        assert len(anomalies) > 0
        assert any(a["type"] == "volume_spike" for a in anomalies)

        # Verify updated metrics reflect the burst
        updated_metrics = analytics.get_metrics(community_id="community-analytics")
        assert updated_metrics["total_items"] == 25
        assert updated_metrics["pending_count"] == 25

    def test_moderation_analytics_resolution_rate(self, moderation_service, analytics):
        """Test resolution rate calculation in analytics."""
        # Create and resolve some items
        for i in range(4):
            item = ModerationItem(
                id=f"rate-item-{i}",
                community_id="community-rate",
                content_id=f"rate-content-{i}",
                content_type="post",
                author_id=f"rate-user-{i}",
                reason="spam",
                status=ModerationStatus.PENDING,
                created_at=datetime.utcnow(),
            )
            moderation_service.create_item(item)

        # Resolve 2 out of 4
        moderation_service.resolve_item(
            item_id="rate-item-0",
            action=ModerationAction.APPROVE,
            moderator_id="mod-001",
        )
        moderation_service.resolve_item(
            item_id="rate-item-1",
            action=ModerationAction.REJECT,
            moderator_id="mod-001",
        )

        metrics = analytics.get_metrics(community_id="community-rate")
        assert metrics["total_items"] == 4
        assert metrics["resolved_count"] == 2
        assert metrics["pending_count"] == 2
        assert metrics["resolution_rate"] == 0.5

    def test_moderation_analytics_time_based_metrics(self, moderation_service, analytics):
        """Test time-based analytics (items per hour)."""
        now = datetime.utcnow()

        # Create items at different times
        for i in range(3):
            item = ModerationItem(
                id=f"time-item-{i}",
                community_id="community-time",
                content_id=f"time-content-{i}",
                content_type="post",
                author_id=f"time-user-{i}",
                reason="spam",
                status=ModerationStatus.PENDING,
                created_at=now - timedelta(hours=i * 2),
            )
            moderation_service.create_item(item)

        metrics = analytics.get_metrics(community_id="community-time")
        assert "items_per_hour" in metrics
        assert metrics["total_items"] == 3
