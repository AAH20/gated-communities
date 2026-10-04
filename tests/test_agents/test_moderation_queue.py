"""
Comprehensive agent tests for the moderation queue system.

Tests cover:
- add_to_queue: Adding items to the moderation queue
- get_queue_status: Retrieving queue status and metrics
- process_queue_item: Processing individual queue items
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from gated_communities.moderation_queue import (
    add_to_queue,
    get_queue_status,
    process_queue_item,
    ModerationQueueError,
    QueueItemNotFoundError,
    QueueItemAlreadyProcessedError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Provide a mock database connection."""
    db = Mock()
    db.execute = Mock()
    db.fetchone = Mock()
    db.fetchall = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def mock_logger():
    """Provide a mock logger."""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def sample_queue_item():
    """Provide a sample queue item for testing."""
    return {
        "id": str(uuid4()),
        "community_id": str(uuid4()),
        "user_id": str(uuid4()),
        "content_id": str(uuid4()),
        "content_type": "post",
        "reason": "spam",
        "priority": 1,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "processed_at": None,
        "processed_by": None,
        "metadata": {"source": "auto_moderation", "confidence": 0.95},
    }


@pytest.fixture
def sample_processed_item():
    """Provide a sample already-processed queue item."""
    return {
        "id": str(uuid4()),
        "community_id": str(uuid4()),
        "user_id": str(uuid4()),
        "content_id": str(uuid4()),
        "content_type": "comment",
        "reason": "harassment",
        "priority": 2,
        "status": "approved",
        "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        "updated_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        "processed_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        "processed_by": str(uuid4()),
        "metadata": {"source": "user_report", "confidence": 0.78},
    }


@pytest.fixture
def mock_queue_service(mock_db, mock_logger):
    """Provide a mock queue service with common setup."""
    service = Mock()
    service.db = mock_db
    service.logger = mock_logger
    return service


# ---------------------------------------------------------------------------
# Tests for add_to_queue
# ---------------------------------------------------------------------------


class TestAddToQueue:
    """Tests for the add_to_queue function."""

    def test_add_to_queue_success(self, mock_db, mock_logger, sample_queue_item):
        """Test successfully adding an item to the moderation queue."""
        mock_db.execute.return_value = None
        mock_db.fetchone.return_value = sample_queue_item

        result = add_to_queue(
            db=mock_db,
            logger=mock_logger,
            community_id=sample_queue_item["community_id"],
            user_id=sample_queue_item["user_id"],
            content_id=sample_queue_item["content_id"],
            content_type=sample_queue_item["content_type"],
            reason=sample_queue_item["reason"],
            priority=sample_queue_item["priority"],
            metadata=sample_queue_item["metadata"],
        )

        assert result is not None
        assert result["community_id"] == sample_queue_item["community_id"]
        assert result["user_id"] == sample_queue_item["user_id"]
        assert result["content_id"] == sample_queue_item["content_id"]
        assert result["content_type"] == sample_queue_item["content_type"]
        assert result["reason"] == sample_queue_item["reason"]
        assert result["priority"] == sample_queue_item["priority"]
        assert result["status"] == "pending"
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_logger.info.assert_called()

    def test_add_to_queue_with_minimal_params(self, mock_db, mock_logger):
        """Test adding an item with only required parameters."""
        mock_db.execute.return_value = None
        mock_db.fetchone.return_value = {
            "id": str(uuid4()),
            "community_id": str(uuid4()),
            "user_id": str(uuid4()),
            "content_id": str(uuid4()),
            "content_type": "post",
            "reason": "spam",
            "priority": 5,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "processed_at": None,
            "processed_by": None,
            "metadata": {},
        }

        result = add_to_queue(
            db=mock_db,
            logger=mock_logger,
            community_id=str(uuid4()),
            user_id=str(uuid4()),
            content_id=str(uuid4()),
            content_type="post",
            reason="spam",
        )

        assert result is not None
        assert result["status"] == "pending"
        assert result["priority"] == 5  # default priority
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_add_to_queue_with_high_priority(self, mock_db, mock_logger):
        """Test adding an item with high priority (lower number = higher priority)."""
        mock_db.execute.return_value = None
        mock_db.fetchone.return_value = {
            "id": str(uuid4()),
            "community_id": str(uuid4()),
            "user_id": str(uuid4()),
            "content_id": str(uuid4()),
            "content_type": "comment",
            "reason": "hate_speech",
            "priority": 0,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "processed_at": None,
            "processed_by": None,
            "metadata": {"urgent": True},
        }

        result = add_to_queue(
            db=mock_db,
            logger=mock_logger,
            community_id=str(uuid4()),
            user_id=str(uuid4()),
            content_id=str(uuid4()),
            content_type="comment",
            reason="hate_speech",
            priority=0,
            metadata={"urgent": True},
        )

        assert result is not None
        assert result["priority"] == 0
        assert result["metadata"]["urgent"] is True

    def test_add_to_queue_with_metadata(self, mock_db, mock_logger):
        """Test adding an item with rich metadata."""
        mock_db.execute.return_value = None
        metadata = {
            "source": "auto_moderation",
            "confidence": 0.92,
            "model_version": "v2.1",
            "flags": ["spam", "low_quality"],
        }
        mock_db.fetchone.return_value = {
            "id": str(uuid4()),
            "community_id": str(uuid4()),
            "user_id": str(uuid4()),
            "content_id": str(uuid4()),
            "content_type": "post",
            "reason": "spam",
            "priority": 1,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "processed_at": None,
            "processed_by": None,
            "metadata": metadata,
        }

        result = add_to_queue(
            db=mock_db,
            logger=mock_logger,
            community_id=str(uuid4()),
            user_id=str(uuid4()),
            content_id=str(uuid4()),
            content_type="post",
            reason="spam",
            priority=1,
            metadata=metadata,
        )

        assert result is not None
        assert result["metadata"]["source"] == "auto_moderation"
        assert result["metadata"]["confidence"] == 0.92
        assert result["metadata"]["model_version"] == "v2.1"
        assert "spam" in result["metadata"]["flags"]

    def test_add_to_queue_db_error(self, mock_db, mock_logger):
        """Test handling of database errors during add."""
        mock_db.execute.side_effect = Exception("Database connection lost")
        mock_db.rollback.return_value = None

        with pytest.raises(ModerationQueueError):
            add_to_queue(
                db=mock_db,
                logger=mock_logger,
                community_id=str(uuid4()),
                user_id=str(uuid4()),
                content_id=str(uuid4()),
                content_type="post",
                reason="spam",
            )

        mock_db.rollback.assert_called_once()
        mock_logger.error.assert_called()

    def test_add_to_queue_duplicate_detection(self, mock_db, mock_logger):
        """Test that duplicate items are handled appropriately."""
        mock_db.execute.side_effect = Exception("Duplicate entry detected")

        with pytest.raises(ModerationQueueError):
            add_to_queue(
                db=mock_db,
                logger=mock_logger,
                community_id=str(uuid4()),
                user_id=str(uuid4()),
                content_id=str(uuid4()),
                content_type="post",
                reason="spam",
            )

    def test_add_to_queue_different_content_types(self, mock_db, mock_logger):
        """Test adding items with various content types."""
        content_types = ["post", "comment", "message", "image", "video"]

        for content_type in content_types:
            mock_db.execute.reset_mock()
            mock_db.fetchone.reset_mock()
            mock_db.execute.return_value = None
            mock_db.fetchone.return_value = {
                "id": str(uuid4()),
                "community_id": str(uuid4()),
                "user_id": str(uuid4()),
                "content_id": str(uuid4()),
                "content_type": content_type,
                "reason": "spam",
                "priority": 3,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "processed_at": None,
                "processed_by": None,
                "metadata": {},
            }

            result = add_to_queue(
                db=mock_db,
                logger=mock_logger,
                community_id=str(uuid4()),
                user_id=str(uuid4()),
                content_id=str(uuid4()),
                content_type=content_type,
                reason="spam",
            )

            assert result is not None
            assert result["content_type"] == content_type

    def test_add_to_queue_generates_uuid(self, mock_db, mock_logger):
        """Test that add_to_queue generates a UUID for the queue item."""
        mock_db.execute.return_value = None
        mock_db.fetchone.return_value = {
            "id": "test-uuid-1234",
            "community_id": str(uuid4()),
            "user_id": str(uuid4()),
            "content_id": str(uuid4()),
            "content_type": "post",
            "reason": "spam",
            "priority": 5,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "processed_at": None,
            "processed_by": None,
            "metadata": {},
        }

        result = add_to_queue(
            db=mock_db,
            logger=mock_logger,
            community_id=str(uuid4()),
            user_id=str(uuid4()),
            content_id=str(uuid4()),
            content_type="post",
            reason="spam",
        )

        assert result is not None
        assert "id" in result
        assert result["id"] == "test-uuid-1234"


# ---------------------------------------------------------------------------
# Tests for get_queue_status
# ---------------------------------------------------------------------------


class TestGetQueueStatus:
    """Tests for the get_queue_status function."""

    def test_get_queue_status_success(self, mock_db, mock_logger):
        """Test successfully retrieving queue status."""
        mock_db.fetchone.return_value = {
            "total_pending": 15,
            "total_processing": 3,
            "total_approved": 120,
            "total_rejected": 45,
            "avg_processing_time_minutes": 12.5,
            "oldest_pending_minutes": 180,
        }

        result = get_queue_status(
            db=mock_db,
            logger=mock_logger,
        )

        assert result is not None
        assert result["total_pending"] == 15
        assert result["total_processing"] == 3
        assert result["total_approved"] == 120
        assert result["total_rejected"] == 45
        assert result["avg_processing_time_minutes"] == 12.5
        assert result["oldest_pending_minutes"] == 180
        mock_db.execute.assert_called_once()

    def test_get_queue_status_empty_queue(self, mock_db, mock_logger):
        """Test queue status when queue is empty."""
        mock_db.fetchone.return_value = {
            "total_pending": 0,
            "total_processing": 0,
            "total_approved": 0,
            "total_rejected": 0,
            "avg_processing_time_minutes": 0,
            "oldest_pending_minutes": 0,
        }

        result = get_queue_status(
            db=mock_db,
            logger=mock_logger,
        )

        assert result is not None
        assert result["total_pending"] == 0
        assert result["total_processing"] == 0
        assert result["total_approved"] == 0
        assert result["total_rejected"] == 0

    def test_get_queue_status_with_community_filter(self, mock_db, mock_logger):
        """Test queue status filtered by community."""
        community_id = str(uuid4())
        mock_db.fetchone.return_value = {
            "total_pending": 5,
            "total_processing": 1,
            "total_approved": 30,
            "total_rejected": 10,
            "avg_processing_time_minutes": 8.0,
            "oldest_pending_minutes": 45,
        }

        result = get_queue_status(
            db=mock_db,
            logger=mock_logger,
            community_id=community_id,
        )

        assert result is not None
        assert result["total_pending"] == 5
        assert result["total_processing"] == 1
        mock_db.execute.assert_called_once()

    def test_get_queue_status_with_status_filter(self, mock_db, mock_logger):
        """Test queue status filtered by status."""
        mock_db.fetchone.return_value = {
            "total_pending": 10,
            "total_processing": 2,
            "total_approved": 0,
            "total_rejected": 0,
            "avg_processing_time_minutes": 5.0,
            "oldest_pending_minutes": 30,
        }

        result = get_queue_status(
            db=mock_db,
            logger=mock_logger,
            status="pending",
        )

        assert result is not None
        assert result["total_pending"] == 10
        assert result["total_processing"] == 2

    def test_get_queue_status_db_error(self, mock_db, mock_logger):
        """Test handling of database errors during status retrieval."""
        mock_db.execute.side_effect = Exception("Query timeout")

        with pytest.raises(ModerationQueueError):
            get_queue_status(
                db=mock_db,
                logger=mock_logger,
            )

        mock_logger.error.assert_called()

    def test_get_queue_status_returns_all_metrics(self, mock_db, mock_logger):
        """Test that all expected metrics are returned."""
        mock_db.fetchone.return_value = {
            "total_pending": 25,
            "total_processing": 5,
            "total_approved": 200,
            "total_rejected": 80,
            "avg_processing_time_minutes": 15.3,
            "oldest_pending_minutes": 240,
        }

        result = get_queue_status(
            db=mock_db,
            logger=mock_logger,
        )

        expected_keys = [
            "total_pending",
            "total_processing",
            "total_approved",
            "total_rejected",
            "avg_processing_time_minutes",
            "oldest_pending_minutes",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_get_queue_status_with_priority_breakdown(self, mock_db, mock_logger):
        """Test queue status with priority breakdown."""
        mock_db.fetchone.return_value = {
            "total_pending": 20,
            "total_processing": 4,
            "total_approved": 150,
            "total_rejected": 60,
            "avg_processing_time_minutes": 10.0,
            "oldest_pending_minutes": 120,
            "priority_breakdown": {
                "high": 5,
                "medium": 10,
                "low": 5,
            },
        }

        result = get_queue_status(
            db=mock_db,
            logger=mock_logger,
        )

        assert result is not None
        assert "priority_breakdown" in result
        assert result["priority_breakdown"]["high"] == 5
        assert result["priority_breakdown"]["medium"] == 10
        assert result["priority_breakdown"]["low"] == 5

    def test_get_queue_status_large_queue(self, mock_db, mock_logger):
        """Test queue status with a large number of items."""
        mock_db.fetchone.return_value = {
            "total_pending": 10000,
            "total_processing": 50,
            "total_approved": 50000,
            "total_rejected": 20000,
            "avg_processing_time_minutes": 20.0,
            "oldest_pending_minutes": 1440,
        }

        result = get_queue_status(
            db=mock_db,
            logger=mock_logger,
        )

        assert result is not None
        assert result["total_pending"] == 10000
        assert result["total_approved"] == 50000
        assert result["total_rejected"] == 20000


# ---------------------------------------------------------------------------
# Tests for process_queue_item
# ---------------------------------------------------------------------------


class TestProcessQueueItem:
    """Tests for the process_queue_item function."""

    def test_process_queue_item_approve(self, mock_db, mock_logger, sample_queue_item):
        """Test approving a queue item."""
        mock_db.fetchone.return_value = sample_queue_item
        mock_db.execute.return_value = None

        result = process_queue_item(
            db=mock_db,
            logger=mock_logger,
            item_id=sample_queue_item["id"],
            action="approved",
            moderator_id=str(uuid4()),
        )

        assert result is not None
        assert result["status"] == "approved"
        assert result["processed_at"] is not None
        assert result["processed_by"] is not None
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()
        mock_logger.info.assert_called()

    def test_process_queue_item_reject(self, mock_db, mock_logger, sample_queue_item):
        """Test rejecting a queue item."""
        mock_db.fetchone.return_value = sample_queue_item
        mock_db.execute.return_value = None

        result = process_queue_item(
            db=mock_db,
            logger=mock_logger,
            item_id=sample_queue_item["id"],
            action="rejected",
            moderator_id=str(uuid4()),
        )

        assert result is not None
        assert result["status"] == "rejected"
        assert result["processed_at"] is not None
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()

    def test_process_queue_item_not_found(self, mock_db, mock_logger):
        """Test processing a non-existent queue item."""
        mock_db.fetchone.return_value = None

        with pytest.raises(QueueItemNotFoundError):
            process_queue_item(
                db=mock_db,
                logger=mock_logger,
                item_id=str(uuid4()),
                action="approved",
                moderator_id=str(uuid4()),
            )

        mock_logger.error.assert_called()

    def test_process_queue_item_already_processed(
        self, mock_db, mock_logger, sample_processed_item
    ):
        """Test processing an already-processed queue item."""
        mock_db.fetchone.return_value = sample_processed_item

        with pytest.raises(QueueItemAlreadyProcessedError):
            process_queue_item(
                db=mock_db,
                logger=mock_logger,
                item_id=sample_processed_item["id"],
                action="approved",
                moderator_id=str(uuid4()),
            )

        mock_logger.warning.assert_called()

    def test_process_queue_item_with_notes(self, mock_db, mock_logger, sample_queue_item):
        """Test processing a queue item with moderator notes."""
        mock_db.fetchone.return_value = sample_queue_item
        mock_db.execute.return_value = None

        result = process_queue_item(
            db=mock_db,
            logger=mock_logger,
            item_id=sample_queue_item["id"],
            action="approved",
            moderator_id=str(uuid4()),
            notes="Content reviewed and approved after manual inspection.",
        )

        assert result is not None
        assert result["status"] == "approved"
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()

    def test_process_queue_item_db_error(self, mock_db, mock_logger, sample_queue_item):
        """Test handling of database errors during processing."""
        mock_db.fetchone.return_value = sample_queue_item
        mock_db.execute.side_effect = Exception("Database write error")
        mock_db.rollback.return_value = None

        with pytest.raises(ModerationQueueError):
            process_queue_item(
                db=mock_db,
                logger=mock_logger,
                item_id=sample_queue_item["id"],
                action="approved",
                moderator_id=str(uuid4()),
            )

        mock_db.rollback.assert_called_once()
        mock_logger.error.assert_called()

    def test_process_queue_item_escalate(self, mock_db, mock_logger, sample_queue_item):
        """Test escalating a queue item."""
        mock_db.fetchone.return_value = sample_queue_item
        mock_db.execute.return_value = None

        result = process_queue_item(
            db=mock_db,
            logger=mock_logger,
            item_id=sample_queue_item["id"],
            action="escalated",
            moderator_id=str(uuid4()),
        )

        assert result is not None
        assert result["status"] == "escalated"
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()

    def test_process_queue_item_dismiss(self, mock_db, mock_logger, sample_queue_item):
        """Test dismissing a queue item (false positive)."""
        mock_db.fetchone.return_value = sample_queue_item
        mock_db.execute.return_value = None

        result = process_queue_item(
            db=mock_db,
            logger=mock_logger,
            item_id=sample_queue_item["id"],
            action="dismissed",
            moderator_id=str(uuid4()),
        )

        assert result is not None
        assert result["status"] == "dismissed"
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()

    def test_process_queue_item_updates_timestamp(
        self, mock_db, mock_logger, sample_queue_item
    ):
        """Test that processing updates the processed_at timestamp."""
        mock_db.fetchone.return_value = sample_queue_item
        mock_db.execute.return_value = None

        before = datetime.utcnow()
        result = process_queue_item(
            db=mock_db,
            logger=mock_logger,
            item_id=sample_queue_item["id"],
            action="approved",
            moderator_id=str(uuid4()),
        )
        after = datetime.utcnow()

        assert result is not None
        assert result["processed_at"] is not None
        processed_time = datetime.fromisoformat(result["processed_at"])
        assert before <= processed_time <= after

    def test_process_queue_item_sets_processed_by(
        self, mock_db, mock_logger, sample_queue_item
    ):
        """Test that processing sets the processed_by field."""
        mock_db.fetchone.return_value = sample_queue_item
        mock_db.execute.return_value = None
        moderator_id = str(uuid4())

        result = process_queue_item(
            db=mock_db,
            logger=mock_logger,
            item_id=sample_queue_item["id"],
            action="approved",
            moderator_id=moderator_id,
        )

        assert result is not None
        assert result["processed_by"] == moderator_id

    def test_process_queue_item_moderator_id_required(
        self, mock_db, mock_logger, sample_queue_item
    ):
        """Test that moderator_id is required for processing."""
        mock_db.fetchone.return_value = sample_queue_item

        with pytest.raises(ValueError):
            process_queue_item(
                db=mock_db,
                logger=mock_logger,
                item_id=sample_queue_item["id"],
                action="approved",
                moderator_id=None,
            )

    def test_process_queue_item_invalid_action(
        self, mock_db, mock_logger, sample_queue_item
    ):
        """Test that invalid actions are rejected."""
        mock_db.fetchone.return_value = sample_queue_item

        with pytest.raises(ValueError):
            process_queue_item(
                db=mock_db,
                logger=mock_logger,
                item_id=sample_queue_item["id"],
                action="invalid_action",
                moderator_id=str(uuid4()),
            )

    def test_process_queue_item_approve_with_metadata_update(
        self, mock_db, mock_logger, sample_queue_item
    ):
        """Test approving an item and updating its metadata."""
        mock_db.fetchone.return_value = sample_queue_item
        mock_db.execute.return_value = None

        result = process_queue_item(
            db=mock_db,
            logger=mock_logger,
            item_id=sample_queue_item["id"],
            action="approved",
            moderator_id=str(uuid4()),
            metadata={"review_time_seconds": 45, "moderator_notes": "Looks fine"},
        )

        assert result is not None
        assert result["status"] == "approved"
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()

    def test_process_queue_item_concurrent_modification(
        self, mock_db, mock_logger, sample_queue_item
    ):
        """Test handling of concurrent modification (item changed since fetch)."""
        mock_db.fetchone.return_value = sample_queue_item
        mock_db.execute.side_effect = Exception("Concurrent modification detected")
        mock_db.rollback.return_value = None

        with pytest.raises(ModerationQueueError):
            process_queue_item(
                db=mock_db,
                logger=mock_logger,
                item_id=sample_queue_item["id"],
                action="approved",
                moderator_id=str(uuid4()),
            )

        mock_db.rollback.assert_called_once()
        mock_logger.error.assert_called()


# ---------------------------------------------------------------------------
# Integration-style tests
# ---------------------------------------------------------------------------


class TestModerationQueueIntegration:
    """Integration-style tests combining multiple operations."""

    def test_full_queue_lifecycle(self, mock_db, mock_logger):
        """Test the full lifecycle: add -> get status -> process."""
        # Step 1: Add item to queue
        item_id = str(uuid4())
        mock_db.execute.return_value = None
        mock_db.fetchone.return_value = {
            "id": item_id,
            "community_id": str(uuid4()),
            "user_id": str(uuid4()),
            "content_id": str(uuid4()),
            "content_type": "post",
            "reason": "spam",
            "priority": 1,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "processed_at": None,
            "processed_by": None,
            "metadata": {},
        }

        added_item = add_to_queue(
            db=mock_db,
            logger=mock_logger,
            community_id=str(uuid4()),
            user_id=str(uuid4()),
            content_id=str(uuid4()),
            content_type="post",
            reason="spam",
        )
        assert added_item["status"] == "pending"

        # Step 2: Check queue status
        mock_db.fetchone.return_value = {
            "total_pending": 1,
            "total_processing": 0,
            "total_approved": 0,
            "total_rejected": 0,
            "avg_processing_time_minutes": 0,
            "oldest_pending_minutes": 0,
        }
        status = get_queue_status(db=mock_db, logger=mock_logger)
        assert status["total_pending"] == 1

        # Step 3: Process the item
        mock_db.fetchone.return_value = added_item
        processed_item = process_queue_item(
            db=mock_db,
            logger=mock_logger,
            item_id=item_id,
            action="approved",
            moderator_id=str(uuid4()),
        )
        assert processed_item["status"] == "approved"
        assert processed_item["processed_at"] is not None

    def test_multiple_items_queue_ordering(self, mock_db, mock_logger):
        """Test that multiple items are processed in priority order."""
        items = []
        for i in range(5):
            item = {
                "id": str(uuid4()),
                "community_id": str(uuid4()),
                "user_id": str(uuid4()),
                "content_id": str(uuid4()),
                "content_type": "post",
                "reason": "spam",
                "priority": i,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "processed_at": None,
                "processed_by": None,
                "metadata": {},
            }
            items.append(item)

        # Add all items
        for item in items:
            mock_db.execute.return_value = None
            mock_db.fetchone.return_value = item
            add_to_queue(
                db=mock_db,
                logger=mock_logger,
                community_id=item["community_id"],
                user_id=item["user_id"],
                content_id=item["content_id"],
                content_type=item["content_type"],
                reason=item["reason"],
                priority=item["priority"],
            )

        # Verify all were added
        assert mock_db.execute.call_count == 5

    def test_queue_status_reflects_changes(self, mock_db, mock_logger):
        """Test that queue status accurately reflects item changes."""
        # Initial status: empty queue
        mock_db.fetchone.return_value = {
            "total_pending": 0,
            "total_processing": 0,
            "total_approved": 0,
            "total_rejected": 0,
            "avg_processing_time_minutes": 0,
            "oldest_pending_minutes": 0,
        }
        status = get_queue_status(db=mock_db, logger=mock_logger)
        assert status["total_pending"] == 0

        # Add an item
        mock_db.execute.return_value = None
        mock_db.fetchone.return_value = {
            "id": str(uuid4()),
            "community_id": str(uuid4()),
            "user_id": str(uuid4()),
            "content_id": str(uuid4()),
            "content_type": "post",
            "reason": "spam",
            "priority": 1,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "processed_at": None,
            "processed_by": None,
            "metadata": {},
        }
        add_to_queue(
            db=mock_db,
            logger=mock_logger,
            community_id=str(uuid4()),
            user_id=str(uuid4()),
            content_id=str(uuid4()),
            content_type="post",
            reason="spam",
        )

        # Status should now show 1 pending
        mock_db.fetchone.return_value = {
            "total_pending": 1,
            "total_processing": 0,
            "total_approved": 0,
            "total_rejected": 0,
            "avg_processing_time_minutes": 0,
            "oldest_pending_minutes": 0,
        }
        status = get_queue_status(db=mock_db, logger=mock_logger)
        assert status["total_pending"] == 1
