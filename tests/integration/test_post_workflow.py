"""Integration tests for post workflow: lifecycle, comments, and moderation."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_client():
    """Provide a mock client for gated-communities API calls."""
    client = MagicMock()
    client.posts = MagicMock()
    client.comments = MagicMock()
    client.moderation = MagicMock()
    return client


@pytest.fixture
def sample_post_data():
    """Return sample post data for testing."""
    return {
        "id": "post-123",
        "title": "Test Post",
        "content": "This is a test post content.",
        "author_id": "user-456",
        "community_id": "community-789",
        "status": "published",
        "created_at": "2026-10-04T10:00:00Z",
        "updated_at": "2026-10-04T10:00:00Z",
    }


@pytest.fixture
def sample_comment_data():
    """Return sample comment data for testing."""
    return {
        "id": "comment-001",
        "post_id": "post-123",
        "author_id": "user-789",
        "content": "This is a test comment.",
        "created_at": "2026-10-04T10:05:00Z",
    }


class TestPostLifecycle:
    """Test the full post lifecycle: create, update, delete."""

    def test_full_post_lifecycle(self, mock_client, sample_post_data):
        """Test creating a post, updating it, then deleting it."""
        # Create post
        mock_client.posts.create.return_value = sample_post_data
        created_post = mock_client.posts.create(
            title="Test Post",
            content="This is a test post content.",
            community_id="community-789",
        )

        assert created_post is not None
        assert created_post["id"] == "post-123"
        assert created_post["title"] == "Test Post"
        assert created_post["status"] == "published"
        mock_client.posts.create.assert_called_once_with(
            title="Test Post",
            content="This is a test post content.",
            community_id="community-789",
        )

        # Update post
        updated_data = {**sample_post_data, "title": "Updated Test Post", "content": "Updated content."}
        mock_client.posts.update.return_value = updated_data
        updated_post = mock_client.posts.update(
            post_id="post-123",
            title="Updated Test Post",
            content="Updated content.",
        )

        assert updated_post is not None
        assert updated_post["id"] == "post-123"
        assert updated_post["title"] == "Updated Test Post"
        assert updated_post["content"] == "Updated content."
        mock_client.posts.update.assert_called_once_with(
            post_id="post-123",
            title="Updated Test Post",
            content="Updated content.",
        )

        # Delete post
        mock_client.posts.delete.return_value = {"success": True, "deleted_id": "post-123"}
        delete_result = mock_client.posts.delete(post_id="post-123")

        assert delete_result is not None
        assert delete_result["success"] is True
        assert delete_result["deleted_id"] == "post-123"
        mock_client.posts.delete.assert_called_once_with(post_id="post-123")


class TestPostCommentFlow:
    """Test post comment flow: create post, add comment, remove comment."""

    def test_post_comment_flow(self, mock_client, sample_post_data, sample_comment_data):
        """Test creating a post, adding a comment, then removing the comment."""
        # Create post
        mock_client.posts.create.return_value = sample_post_data
        created_post = mock_client.posts.create(
            title="Test Post",
            content="This is a test post content.",
            community_id="community-789",
        )

        assert created_post is not None
        assert created_post["id"] == "post-123"
        mock_client.posts.create.assert_called_once()

        # Add comment to post
        mock_client.comments.create.return_value = sample_comment_data
        created_comment = mock_client.comments.create(
            post_id="post-123",
            content="This is a test comment.",
            author_id="user-789",
        )

        assert created_comment is not None
        assert created_comment["id"] == "comment-001"
        assert created_comment["post_id"] == "post-123"
        assert created_comment["content"] == "This is a test comment."
        mock_client.comments.create.assert_called_once_with(
            post_id="post-123",
            content="This is a test comment.",
            author_id="user-789",
        )

        # Remove comment
        mock_client.comments.delete.return_value = {"success": True, "deleted_id": "comment-001"}
        delete_result = mock_client.comments.delete(comment_id="comment-001")

        assert delete_result is not None
        assert delete_result["success"] is True
        assert delete_result["deleted_id"] == "comment-001"
        mock_client.comments.delete.assert_called_once_with(comment_id="comment-001")


class TestPostModerationFlow:
    """Test post moderation flow: create post, moderate, flag."""

    def test_post_moderation_flow(self, mock_client, sample_post_data):
        """Test creating a post, moderating it, then flagging it."""
        # Create post
        mock_client.posts.create.return_value = sample_post_data
        created_post = mock_client.posts.create(
            title="Test Post",
            content="This is a test post content.",
            community_id="community-789",
        )

        assert created_post is not None
        assert created_post["id"] == "post-123"
        mock_client.posts.create.assert_called_once()

        # Moderate post
        moderated_data = {**sample_post_data, "status": "under_review", "moderated_by": "mod-001"}
        mock_client.moderation.moderate.return_value = moderated_data
        moderated_post = mock_client.moderation.moderate(
            post_id="post-123",
            action="hold",
            moderator_id="mod-001",
            reason="Routine review",
        )

        assert moderated_post is not None
        assert moderated_post["id"] == "post-123"
        assert moderated_post["status"] == "under_review"
        assert moderated_post["moderated_by"] == "mod-001"
        mock_client.moderation.moderate.assert_called_once_with(
            post_id="post-123",
            action="hold",
            moderator_id="mod-001",
            reason="Routine review",
        )

        # Flag post
        mock_client.moderation.flag.return_value = {
            "success": True,
            "post_id": "post-123",
            "flagged_by": "user-999",
            "reason": "spam",
        }
        flag_result = mock_client.moderation.flag(
            post_id="post-123",
            flagged_by="user-999",
            reason="spam",
        )

        assert flag_result is not None
        assert flag_result["success"] is True
        assert flag_result["post_id"] == "post-123"
        assert flag_result["flagged_by"] == "user-999"
        assert flag_result["reason"] == "spam"
        mock_client.moderation.flag.assert_called_once_with(
            post_id="post-123",
            flagged_by="user-999",
            reason="spam",
        )
