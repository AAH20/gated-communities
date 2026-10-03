"""Comprehensive service tests for the message service."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.gated_communities.services.message_service import (
    MessageService,
    get_message,
    list_messages,
    create_message,
    update_message,
    delete_message,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Provide a mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest.fixture
def mock_message():
    """Provide a sample message ORM-like object."""
    msg = MagicMock()
    msg.id = 1
    msg.community_id = 10
    msg.author_id = 100
    msg.content = "Hello, world!"
    msg.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    msg.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    msg.is_deleted = False
    return msg


@pytest.fixture
def mock_message_list():
    """Provide a list of sample message objects."""
    messages = []
    for i in range(1, 6):
        msg = MagicMock()
        msg.id = i
        msg.community_id = 10
        msg.author_id = 100 + i
        msg.content = f"Message {i}"
        msg.created_at = datetime(2025, 1, i, tzinfo=timezone.utc)
        msg.updated_at = datetime(2025, 1, i, tzinfo=timezone.utc)
        msg.is_deleted = False
        messages.append(msg)
    return messages


@pytest.fixture
def message_service(mock_db):
    """Provide a MessageService instance with a mock db."""
    return MessageService(db=mock_db)


@pytest.fixture
def sample_create_data():
    """Provide sample data for creating a message."""
    return {
        "community_id": 10,
        "author_id": 100,
        "content": "Test message content",
    }


@pytest.fixture
def sample_update_data():
    """Provide sample data for updating a message."""
    return {
        "content": "Updated message content",
    }


# ---------------------------------------------------------------------------
# Tests for get_message
# ---------------------------------------------------------------------------


class TestGetMessage:
    """Tests for the get_message function."""

    @pytest.mark.asyncio
    async def test_get_message_success(self, mock_db, mock_message):
        """Test that get_message returns a message when it exists."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_message)
        )

        result = await get_message(db=mock_db, message_id=1)

        assert result is not None
        assert result.id == 1
        assert result.community_id == 10
        assert result.author_id == 100
        assert result.content == "Hello, world!"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_message_not_found(self, mock_db):
        """Test that get_message returns None when message does not exist."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        result = await get_message(db=mock_db, message_id=999)

        assert result is None
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_message_deleted(self, mock_db, mock_message):
        """Test that get_message returns None for soft-deleted messages."""
        mock_message.is_deleted = True
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        result = await get_message(db=mock_db, message_id=1)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_message_invalid_id(self, mock_db):
        """Test that get_message handles invalid message IDs gracefully."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        result = await get_message(db=mock_db, message_id=-1)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_message_service_method(self, mock_db, mock_message):
        """Test MessageService.get_message method directly."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_message)
        )
        service = MessageService(db=mock_db)

        result = await service.get_message(message_id=1)

        assert result is not None
        assert result.id == 1
        assert result.content == "Hello, world!"

    @pytest.mark.asyncio
    async def test_get_message_db_error(self, mock_db):
        """Test that get_message propagates database errors."""
        mock_db.execute.side_effect = Exception("Database connection lost")

        with pytest.raises(Exception, match="Database connection lost"):
            await get_message(db=mock_db, message_id=1)


# ---------------------------------------------------------------------------
# Tests for list_messages
# ---------------------------------------------------------------------------


class TestListMessages:
    """Tests for the list_messages function."""

    @pytest.mark.asyncio
    async def test_list_messages_success(self, mock_db, mock_message_list):
        """Test that list_messages returns all messages when no filters applied."""
        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(
                    all=MagicMock(return_value=mock_message_list)
                )
            )
        )

        result = await list_messages(db=mock_db, community_id=10)

        assert result is not None
        assert len(result) == 5
        assert result[0].id == 1
        assert result[4].id == 5
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_messages_empty(self, mock_db):
        """Test that list_messages returns empty list when no messages exist."""
        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(all=MagicMock(return_value=[]))
            )
        )

        result = await list_messages(db=mock_db, community_id=999)

        assert result == []
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_messages_with_author_filter(
        self, mock_db, mock_message_list
    ):
        """Test that list_messages filters by author_id correctly."""
        filtered = [m for m in mock_message_list if m.author_id == 101]
        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(all=MagicMock(return_value=filtered))
            )
        )

        result = await list_messages(
            db=mock_db, community_id=10, author_id=101
        )

        assert len(result) == 1
        assert result[0].author_id == 101

    @pytest.mark.asyncio
    async def test_list_messages_with_pagination(self, mock_db, mock_message_list):
        """Test that list_messages respects skip and limit parameters."""
        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(
                    all=MagicMock(return_value=mock_message_list[1:4])
                )
            )
        )

        result = await list_messages(
            db=mock_db, community_id=10, skip=1, limit=3
        )

        assert len(result) == 3
        assert result[0].id == 2
        assert result[2].id == 4

    @pytest.mark.asyncio
    async def test_list_messages_with_date_range(
        self, mock_db, mock_message_list
    ):
        """Test that list_messages filters by date range."""
        filtered = [
            m
            for m in mock_message_list
            if m.created_at >= datetime(2025, 1, 2, tzinfo=timezone.utc)
        ]
        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(all=MagicMock(return_value=filtered))
            )
        )

        result = await list_messages(
            db=mock_db,
            community_id=10,
            created_after=datetime(2025, 1, 2, tzinfo=timezone.utc),
        )

        assert len(result) == 4
        assert all(
            m.created_at >= datetime(2025, 1, 2, tzinfo=timezone.utc)
            for m in result
        )

    @pytest.mark.asyncio
    async def test_list_messages_with_content_search(
        self, mock_db, mock_message_list
    ):
        """Test that list_messages filters by content search term."""
        filtered = [m for m in mock_message_list if "Message 3" in m.content]
        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(all=MagicMock(return_value=filtered))
            )
        )

        result = await list_messages(
            db=mock_db, community_id=10, content_search="Message 3"
        )

        assert len(result) == 1
        assert "Message 3" in result[0].content

    @pytest.mark.asyncio
    async def test_list_messages_combined_filters(
        self, mock_db, mock_message_list
    ):
        """Test that list_messages applies multiple filters together."""
        filtered = [
            m
            for m in mock_message_list
            if m.author_id == 102 and m.id > 1
        ]
        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(all=MagicMock(return_value=filtered))
            )
        )

        result = await list_messages(
            db=mock_db,
            community_id=10,
            author_id=102,
            skip=0,
            limit=10,
        )

        assert len(result) == 1
        assert result[0].author_id == 102

    @pytest.mark.asyncio
    async def test_list_messages_service_method(
        self, mock_db, mock_message_list
    ):
        """Test MessageService.list_messages method directly."""
        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(
                    all=MagicMock(return_value=mock_message_list)
                )
            )
        )
        service = MessageService(db=mock_db)

        result = await service.list_messages(community_id=10)

        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_list_messages_db_error(self, mock_db):
        """Test that list_messages propagates database errors."""
        mock_db.execute.side_effect = Exception("Query timeout")

        with pytest.raises(Exception, match="Query timeout"):
            await list_messages(db=mock_db, community_id=10)


# ---------------------------------------------------------------------------
# Tests for create_message
# ---------------------------------------------------------------------------


class TestCreateMessage:
    """Tests for the create_message function."""

    @pytest.mark.asyncio
    async def test_create_message_success(
        self, mock_db, mock_message, sample_create_data
    ):
        """Test that create_message creates and returns a new message."""
        mock_db.refresh.side_effect = lambda obj: setattr(
            obj, "id", 1
        ) or setattr(obj, "created_at", datetime(2025, 1, 1, tzinfo=timezone.utc))

        result = await create_message(db=mock_db, **sample_create_data)

        assert result is not None
        assert result.id == 1
        assert result.community_id == 10
        assert result.author_id == 100
        assert result.content == "Test message content"
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_message_with_minimal_data(self, mock_db):
        """Test create_message with only required fields."""
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 2)

        result = await create_message(
            db=mock_db,
            community_id=5,
            author_id=50,
            content="Minimal message",
        )

        assert result.id == 2
        assert result.community_id == 5
        assert result.author_id == 50
        assert result.content == "Minimal message"

    @pytest.mark.asyncio
    async def test_create_message_empty_content(self, mock_db):
        """Test create_message with empty content string."""
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 3)

        result = await create_message(
            db=mock_db,
            community_id=10,
            author_id=100,
            content="",
        )

        assert result.id == 3
        assert result.content == ""

    @pytest.mark.asyncio
    async def test_create_message_long_content(self, mock_db):
        """Test create_message with very long content."""
        long_content = "A" * 10000
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 4)

        result = await create_message(
            db=mock_db,
            community_id=10,
            author_id=100,
            content=long_content,
        )

        assert result.id == 4
        assert len(result.content) == 10000

    @pytest.mark.asyncio
    async def test_create_message_service_method(
        self, mock_db, sample_create_data
    ):
        """Test MessageService.create_message method directly."""
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 5)
        service = MessageService(db=mock_db)

        result = await service.create_message(**sample_create_data)

        assert result.id == 5
        assert result.content == "Test message content"

    @pytest.mark.asyncio
    async def test_create_message_db_error(self, mock_db, sample_create_data):
        """Test that create_message rolls back on database error."""
        mock_db.execute.side_effect = Exception("Insert failed")

        with pytest.raises(Exception, match="Insert failed"):
            await create_message(db=mock_db, **sample_create_data)

        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_message_sets_timestamps(
        self, mock_db, sample_create_data
    ):
        """Test that create_message sets created_at and updated_at."""
        mock_db.refresh.side_effect = lambda obj: (
            setattr(obj, "id", 1),
            setattr(obj, "created_at", datetime(2025, 6, 1, tzinfo=timezone.utc)),
            setattr(obj, "updated_at", datetime(2025, 6, 1, tzinfo=timezone.utc)),
        )

        result = await create_message(db=mock_db, **sample_create_data)

        assert result.created_at is not None
        assert result.updated_at is not None


# ---------------------------------------------------------------------------
# Tests for update_message
# ---------------------------------------------------------------------------


class TestUpdateMessage:
    """Tests for the update_message function."""

    @pytest.mark.asyncio
    async def test_update_message_success(
        self, mock_db, mock_message, sample_update_data
    ):
        """Test that update_message updates and returns the message."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_message)
        )

        result = await update_message(
            db=mock_db, message_id=1, **sample_update_data
        )

        assert result is not None
        assert result.id == 1
        assert result.content == "Updated message content"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_message_not_found(self, mock_db, sample_update_data):
        """Test that update_message returns None when message does not exist."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        result = await update_message(
            db=mock_db, message_id=999, **sample_update_data
        )

        assert result is None
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_message_partial_update(self, mock_db, mock_message):
        """Test that update_message allows partial updates."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_message)
        )

        result = await update_message(
            db=mock_db, message_id=1, content="Only content updated"
        )

        assert result is not None
        assert result.content == "Only content updated"
        assert result.community_id == 10
        assert result.author_id == 100

    @pytest.mark.asyncio
    async def test_update_message_no_changes(self, mock_db, mock_message):
        """Test update_message with no actual changes."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_message)
        )

        result = await update_message(
            db=mock_db, message_id=1, content="Hello, world!"
        )

        assert result is not None
        assert result.content == "Hello, world!"

    @pytest.mark.asyncio
    async def test_update_message_service_method(
        self, mock_db, mock_message, sample_update_data
    ):
        """Test MessageService.update_message method directly."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_message)
        )
        service = MessageService(db=mock_db)

        result = await service.update_message(
            message_id=1, **sample_update_data
        )

        assert result is not None
        assert result.content == "Updated message content"

    @pytest.mark.asyncio
    async def test_update_message_db_error(
        self, mock_db, mock_message, sample_update_data
    ):
        """Test that update_message rolls back on database error."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_message)
        )
        mock_db.commit.side_effect = Exception("Update failed")

        with pytest.raises(Exception, match="Update failed"):
            await update_message(
                db=mock_db, message_id=1, **sample_update_data
            )

        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_message_updates_timestamp(
        self, mock_db, mock_message
    ):
        """Test that update_message updates the updated_at timestamp."""
        original_updated_at = mock_message.updated_at
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_message)
        )

        result = await update_message(
            db=mock_db, message_id=1, content="New content"
        )

        assert result.updated_at >= original_updated_at


# ---------------------------------------------------------------------------
# Tests for delete_message
# ---------------------------------------------------------------------------


class TestDeleteMessage:
    """Tests for the delete_message function."""

    @pytest.mark.asyncio
    async def test_delete_message_success(self, mock_db, mock_message):
        """Test that delete_message removes a message and returns True."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_message)
        )

        result = await delete_message(db=mock_db, message_id=1)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_message)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_message_not_found(self, mock_db):
        """Test that delete_message returns False when message does not exist."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        result = await delete_message(db=mock_db, message_id=999)

        assert result is False
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_message_service_method(self, mock_db, mock_message):
        """Test MessageService.delete_message method directly."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_message)
        )
        service = MessageService(db=mock_db)

        result = await service.delete_message(message_id=1)

        assert result is True
        mock_db.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_message_db_error(self, mock_db, mock_message):
        """Test that delete_message rolls back on database error."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_message)
        )
        mock_db.commit.side_effect = Exception("Delete failed")

        with pytest.raises(Exception, match="Delete failed"):
            await delete_message(db=mock_db, message_id=1)

        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_message_already_deleted(
        self, mock_db, mock_message
    ):
        """Test that delete_message handles already soft-deleted messages."""
        mock_message.is_deleted = True
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        result = await delete_message(db=mock_db, message_id=1)

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_message_cascades(self, mock_db, mock_message):
        """Test that delete_message properly removes the message from db."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_message)
        )

        await delete_message(db=mock_db, message_id=1)

        mock_db.delete.assert_called_once_with(mock_message)
        mock_db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Integration-style tests
# ---------------------------------------------------------------------------


class TestMessageServiceIntegration:
    """Integration-style tests combining multiple operations."""

    @pytest.mark.asyncio
    async def test_full_message_lifecycle(
        self, mock_db, sample_create_data, sample_update_data
    ):
        """Test the complete lifecycle: create → get → update → delete."""
        # Create
        mock_db.refresh.side_effect = lambda obj: (
            setattr(obj, "id", 1),
            setattr(obj, "created_at", datetime(2025, 1, 1, tzinfo=timezone.utc)),
            setattr(obj, "updated_at", datetime(2025, 1, 1, tzinfo=timezone.utc)),
        )
        created = await create_message(db=mock_db, **sample_create_data)
        assert created.id == 1

        # Get
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=created)
        )
        fetched = await get_message(db=mock_db, message_id=1)
        assert fetched is not None
        assert fetched.content == "Test message content"

        # Update
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=created)
        )
        updated = await update_message(
            db=mock_db, message_id=1, **sample_update_data
        )
        assert updated.content == "Updated message content"

        # Delete
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=created)
        )
        deleted = await delete_message(db=mock_db, message_id=1)
        assert deleted is True

    @pytest.mark.asyncio
    async def test_create_multiple_and_list(
        self, mock_db, sample_create_data
    ):
        """Test creating multiple messages and listing them."""
        messages = []
        for i in range(3):
            msg = MagicMock()
            msg.id = i + 1
            msg.community_id = 10
            msg.author_id = 100
            msg.content = f"Message {i + 1}"
            msg.created_at = datetime(2025, 1, i + 1, tzinfo=timezone.utc)
            msg.updated_at = datetime(2025, 1, i + 1, tzinfo=timezone.utc)
            msg.is_deleted = False
            messages.append(msg)

        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(all=MagicMock(return_value=messages))
            )
        )

        result = await list_messages(db=mock_db, community_id=10)

        assert len(result) == 3
        assert [m.id for m in result] == [1, 2, 3]
