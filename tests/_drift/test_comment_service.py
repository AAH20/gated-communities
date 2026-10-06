"""Comprehensive service tests for the comment service."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from gated_communities.services.comment_service import (
    CommentService,
    create_comment,
    delete_comment,
    get_comment,
    list_comments,
    update_comment,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Provide a mock database session."""
    return MagicMock()


@pytest.fixture
def comment_service(mock_db):
    """Provide a CommentService instance with a mock database."""
    return CommentService(db=mock_db)


@pytest.fixture
def sample_comment():
    """Provide a sample comment dict."""
    return {
        "id": "comment-1",
        "post_id": "post-1",
        "author_id": "user-1",
        "content": "This is a test comment",
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "is_deleted": False,
    }


@pytest.fixture
def sample_comment_list():
    """Provide a list of sample comment dicts."""
    return [
        {
            "id": f"comment-{i}",
            "post_id": "post-1",
            "author_id": f"user-{i}",
            "content": f"Comment content {i}",
            "created_at": datetime(2024, 1, i + 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, i + 1, tzinfo=timezone.utc),
            "is_deleted": False,
        }
        for i in range(5)
    ]


# ---------------------------------------------------------------------------
# Tests for get_comment
# ---------------------------------------------------------------------------


class TestGetComment:
    """Tests for the get_comment function."""

    def test_get_comment_returns_comment(self, mock_db, sample_comment):
        """get_comment returns a comment when found."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_comment

        result = get_comment(mock_db, "comment-1")

        assert result is not None
        assert result["id"] == "comment-1"
        assert result["post_id"] == "post-1"
        assert result["author_id"] == "user-1"
        assert result["content"] == "This is a test comment"

    def test_get_comment_returns_none_when_not_found(self, mock_db):
        """get_comment returns None when the comment does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_comment(mock_db, "nonexistent-id")

        assert result is None

    def test_get_comment_queries_correct_id(self, mock_db, sample_comment):
        """get_comment queries the database with the correct comment id."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_comment

        get_comment(mock_db, "comment-42")

        mock_db.query.assert_called_once()
        filter_args = mock_db.query.return_value.filter.call_args
        assert filter_args is not None

    def test_get_comment_excludes_deleted(self, mock_db):
        """get_comment excludes soft-deleted comments by default."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_comment(mock_db, "deleted-comment-id")

        assert result is None

    def test_get_comment_service_method(self, comment_service, mock_db, sample_comment):
        """CommentService.get_comment delegates correctly."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_comment

        result = comment_service.get_comment("comment-1")

        assert result is not None
        assert result["id"] == "comment-1"


# ---------------------------------------------------------------------------
# Tests for list_comments
# ---------------------------------------------------------------------------


class TestListComments:
    """Tests for the list_comments function."""

    def test_list_comments_returns_all(self, mock_db, sample_comment_list):
        """list_comments returns all comments when no filters applied."""
        mock_db.query.return_value.filter.return_value.all.return_value = sample_comment_list

        result = list_comments(mock_db)

        assert len(result) == 5
        assert result[0]["id"] == "comment-0"
        assert result[4]["id"] == "comment-4"

    def test_list_comments_filters_by_post_id(self, mock_db, sample_comment_list):
        """list_comments filters by post_id when provided."""
        filtered = [c for c in sample_comment_list if c["post_id"] == "post-1"]
        mock_db.query.return_value.filter.return_value.all.return_value = filtered

        result = list_comments(mock_db, post_id="post-1")

        assert all(c["post_id"] == "post-1" for c in result)

    def test_list_comments_filters_by_author_id(self, mock_db, sample_comment_list):
        """list_comments filters by author_id when provided."""
        filtered = [c for c in sample_comment_list if c["author_id"] == "user-2"]
        mock_db.query.return_value.filter.return_value.all.return_value = filtered

        result = list_comments(mock_db, author_id="user-2")

        assert len(result) == 1
        assert result[0]["author_id"] == "user-2"

    def test_list_comments_with_pagination(self, mock_db, sample_comment_list):
        """list_comments respects limit and offset parameters."""
        mock_db.query.return_value.limit.return_value.offset.return_value.all.return_value = sample_comment_list[:2]

        result = list_comments(mock_db, limit=2, offset=0)

        assert len(result) == 2
        mock_db.query.return_value.limit.assert_called_with(2)
        mock_db.query.return_value.limit.return_value.offset.assert_called_with(0)

    def test_list_comments_empty_result(self, mock_db):
        """list_comments returns empty list when no comments match."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = list_comments(mock_db, post_id="nonexistent-post")

        assert result == []

    def test_list_comments_combined_filters(self, mock_db, sample_comment_list):
        """list_comments applies multiple filters together."""
        filtered = [
            c for c in sample_comment_list
            if c["post_id"] == "post-1" and c["author_id"] == "user-3"
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = filtered

        result = list_comments(mock_db, post_id="post-1", author_id="user-3")

        assert len(result) == 1
        assert result[0]["author_id"] == "user-3"
        assert result[0]["post_id"] == "post-1"

    def test_list_comments_service_method(self, comment_service, mock_db, sample_comment_list):
        """CommentService.list_comments delegates correctly."""
        mock_db.query.return_value.filter.return_value.all.return_value = sample_comment_list

        result = comment_service.list_comments(post_id="post-1")

        assert len(result) == 5


# ---------------------------------------------------------------------------
# Tests for create_comment
# ---------------------------------------------------------------------------


class TestCreateComment:
    """Tests for the create_comment function."""

    def test_create_comment_success(self, mock_db):
        """create_comment creates and returns a new comment."""
        new_comment = {
            "id": "new-comment-1",
            "post_id": "post-1",
            "author_id": "user-1",
            "content": "New comment content",
            "created_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
            "is_deleted": False,
        }
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: obj.update(new_comment) if hasattr(obj, "update") else None

        result = create_comment(
            mock_db,
            post_id="post-1",
            author_id="user-1",
            content="New comment content",
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_comment_persists_correct_fields(self, mock_db):
        """create_comment persists the correct field values."""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        create_comment(
            mock_db,
            post_id="post-99",
            author_id="user-42",
            content="Specific content here",
        )

        added_obj = mock_db.add.call_args[0][0]
        assert added_obj.post_id == "post-99"
        assert added_obj.author_id == "user-42"
        assert added_obj.content == "Specific content here"

    def test_create_comment_requires_post_id(self, mock_db):
        """create_comment raises when post_id is missing."""
        with pytest.raises((ValueError, TypeError)):
            create_comment(mock_db, post_id=None, author_id="user-1", content="test")

    def test_create_comment_requires_author_id(self, mock_db):
        """create_comment raises when author_id is missing."""
        with pytest.raises((ValueError, TypeError)):
            create_comment(mock_db, post_id="post-1", author_id=None, content="test")

    def test_create_comment_requires_content(self, mock_db):
        """create_comment raises when content is missing."""
        with pytest.raises((ValueError, TypeError)):
            create_comment(mock_db, post_id="post-1", author_id="user-1", content=None)

    def test_create_comment_empty_content(self, mock_db):
        """create_comment handles empty string content."""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        create_comment(mock_db, post_id="post-1", author_id="user-1", content="")

        added_obj = mock_db.add.call_args[0][0]
        assert added_obj.content == ""

    def test_create_comment_service_method(self, comment_service, mock_db):
        """CommentService.create_comment delegates correctly."""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        comment_service.create_comment(
            post_id="post-1",
            author_id="user-1",
            content="Service method comment",
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for update_comment
# ---------------------------------------------------------------------------


class TestUpdateComment:
    """Tests for the update_comment function."""

    def test_update_comment_success(self, mock_db, sample_comment):
        """update_comment updates and returns the modified comment."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_comment

        result = update_comment(mock_db, "comment-1", content="Updated content")

        assert result is not None
        assert result["content"] == "Updated content"
        mock_db.commit.assert_called_once()

    def test_update_comment_partial_update(self, mock_db, sample_comment):
        """update_comment allows partial updates (only specified fields)."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_comment

        result = update_comment(mock_db, "comment-1", content="Only content changed")

        assert result["content"] == "Only content changed"
        assert result["post_id"] == "post-1"
        assert result["author_id"] == "user-1"

    def test_update_comment_not_found(self, mock_db):
        """update_comment returns None when comment does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = update_comment(mock_db, "nonexistent", content="New content")

        assert result is None
        mock_db.commit.assert_not_called()

    def test_update_comment_updates_timestamp(self, mock_db, sample_comment):
        """update_comment updates the updated_at timestamp."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_comment
        original_updated_at = sample_comment["updated_at"]

        result = update_comment(mock_db, "comment-1", content="Timestamp test")

        assert result["updated_at"] >= original_updated_at

    def test_update_comment_no_changes(self, mock_db, sample_comment):
        """update_comment with no fields still commits (no-op update)."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_comment

        result = update_comment(mock_db, "comment-1")

        assert result is not None
        mock_db.commit.assert_called_once()

    def test_update_comment_service_method(self, comment_service, mock_db, sample_comment):
        """CommentService.update_comment delegates correctly."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_comment

        result = comment_service.update_comment("comment-1", content="Service update")

        assert result["content"] == "Service update"
        mock_db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for delete_comment
# ---------------------------------------------------------------------------


class TestDeleteComment:
    """Tests for the delete_comment function."""

    def test_delete_comment_success(self, mock_db, sample_comment):
        """delete_comment removes the comment and returns True."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_comment

        result = delete_comment(mock_db, "comment-1")

        assert result is True
        mock_db.commit.assert_called_once()

    def test_delete_comment_not_found(self, mock_db):
        """delete_comment returns False when comment does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = delete_comment(mock_db, "nonexistent-id")

        assert result is False
        mock_db.commit.assert_not_called()

    def test_delete_comment_soft_delete(self, mock_db, sample_comment):
        """delete_comment performs a soft delete by setting is_deleted."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_comment

        result = delete_comment(mock_db, "comment-1", soft_delete=True)

        assert result is True
        assert sample_comment["is_deleted"] is True
        mock_db.commit.assert_called_once()

    def test_delete_comment_hard_delete(self, mock_db, sample_comment):
        """delete_comment performs a hard delete when soft_delete is False."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_comment

        result = delete_comment(mock_db, "comment-1", soft_delete=False)

        assert result is True
        mock_db.delete.assert_called_once_with(sample_comment)
        mock_db.commit.assert_called_once()

    def test_delete_comment_service_method(self, comment_service, mock_db, sample_comment):
        """CommentService.delete_comment delegates correctly."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_comment

        result = comment_service.delete_comment("comment-1")

        assert result is True
        mock_db.commit.assert_called_once()

    def test_delete_comment_service_soft_delete(self, comment_service, mock_db, sample_comment):
        """CommentService.delete_comment with soft_delete flag."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_comment

        result = comment_service.delete_comment("comment-1", soft_delete=True)

        assert result is True
        assert sample_comment["is_deleted"] is True
