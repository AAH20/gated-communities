"""Comprehensive service tests for PostService."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from gated_communities.models.post import Post, PostStatus
from gated_communities.services.post_service import PostService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Provide a mock database session."""
    return MagicMock()


@pytest.fixture
def post_service(mock_db):
    """Provide a PostService instance with a mocked DB."""
    return PostService(db=mock_db)


@pytest.fixture
def sample_post():
    """Provide a sample Post instance."""
    return Post(
        id="post-123",
        community_id="comm-456",
        author_id="user-789",
        title="Test Post Title",
        content="This is the test post content.",
        status=PostStatus.PUBLISHED,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_posts_list():
    """Provide a list of sample Post instances."""
    return [
        Post(
            id=f"post-{i}",
            community_id="comm-456",
            author_id=f"user-{i}",
            title=f"Post {i}",
            content=f"Content for post {i}.",
            status=PostStatus.PUBLISHED,
            created_at=datetime(2026, 1, i + 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, i + 1, tzinfo=timezone.utc),
        )
        for i in range(5)
    ]


# ---------------------------------------------------------------------------
# Tests: get_post
# ---------------------------------------------------------------------------


class TestGetPost:
    """Tests for PostService.get_post."""

    def test_get_post(self, post_service, mock_db, sample_post):
        """get_post returns a Post when found, None when not found, and queries correctly."""
        # Test: returns post when found
        mock_db.query.return_value.filter.return_value.first.return_value = sample_post
        result = post_service.get_post("post-123")
        assert result is not None
        assert result.id == "post-123"
        assert result.title == "Test Post Title"
        assert result.content == "This is the test post content."
        assert result.status == PostStatus.PUBLISHED
        mock_db.query.assert_called_once()
        mock_db.query.return_value.filter.assert_called_once()

        # Test: returns None when not found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = post_service.get_post("nonexistent-id")
        assert result is None

        # Test: works with different statuses
        draft_post = Post(
            id="post-draft",
            community_id="comm-456",
            author_id="user-789",
            title="Draft Post",
            content="Draft content.",
            status=PostStatus.DRAFT,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        mock_db.query.return_value.filter.return_value.first.return_value = draft_post
        result = post_service.get_post("post-draft")
        assert result is not None
        assert result.status == PostStatus.DRAFT


# ---------------------------------------------------------------------------
# Tests: list_posts
# ---------------------------------------------------------------------------


class TestListPosts:
    """Tests for PostService.list_posts."""

    def test_list_posts(self, post_service, mock_db, sample_posts_list):
        """list_posts returns all posts, supports filters, pagination, and empty results."""
        # Test: returns all posts
        mock_query = MagicMock()
        mock_query.all.return_value = sample_posts_list
        mock_query.filter.return_value = mock_query
        mock_db.query.return_value = mock_query
        result = post_service.list_posts()
        assert len(result) == 5
        assert all(isinstance(p, Post) for p in result)

        # Test: community filter
        mock_query.reset_mock()
        mock_query.all.return_value = sample_posts_list
        mock_query.filter.return_value = mock_query
        result = post_service.list_posts(community_id="comm-456")
        assert len(result) == 5
        mock_query.filter.assert_called()

        # Test: author filter
        mock_query.reset_mock()
        mock_query.all.return_value = sample_posts_list
        mock_query.filter.return_value = mock_query
        result = post_service.list_posts(author_id="user-0")
        assert len(result) == 5
        mock_query.filter.assert_called()

        # Test: status filter
        mock_query.reset_mock()
        mock_query.all.return_value = sample_posts_list
        mock_query.filter.return_value = mock_query
        result = post_service.list_posts(status=PostStatus.PUBLISHED)
        assert len(result) == 5
        mock_query.filter.assert_called()

        # Test: pagination
        mock_query.reset_mock()
        mock_query.all.return_value = sample_posts_list[:2]
        mock_query.limit.return_value.offset.return_value = mock_query
        result = post_service.list_posts(limit=2, offset=0)
        assert len(result) == 2
        mock_query.limit.assert_called_once_with(2)
        mock_query.limit.return_value.offset.assert_called_once_with(0)

        # Test: empty results
        mock_query.reset_mock()
        mock_query.all.return_value = []
        mock_query.filter.return_value = mock_query
        result = post_service.list_posts(community_id="nonexistent-comm")
        assert result == []

        # Test: multiple filters
        mock_query.reset_mock()
        mock_query.all.return_value = sample_posts_list
        mock_query.filter.return_value = mock_query
        result = post_service.list_posts(
            community_id="comm-456",
            author_id="user-0",
            status=PostStatus.PUBLISHED,
        )
        assert len(result) == 5
        assert mock_query.filter.call_count >= 1


# ---------------------------------------------------------------------------
# Tests: create_post
# ---------------------------------------------------------------------------


class TestCreatePost:
    """Tests for PostService.create_post."""

    def test_create_post(self, post_service, mock_db):
        """create_post creates, persists, and returns a new Post with correct fields."""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", "post-123")

        # Test: basic creation
        result = post_service.create_post(
            community_id="comm-456",
            author_id="user-789",
            title="Test Post Title",
            content="This is the test post content.",
        )
        assert result is not None
        assert result.id == "post-123"
        assert result.community_id == "comm-456"
        assert result.author_id == "user-789"
        assert result.title == "Test Post Title"
        assert result.content == "This is the test post content."
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Test: default status is DRAFT
        assert result.status == PostStatus.DRAFT

        # Test: explicit status
        mock_db.reset_mock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", "post-new")
        result = post_service.create_post(
            community_id="comm-456",
            author_id="user-789",
            title="Published Post",
            content="Published content.",
            status=PostStatus.PUBLISHED,
        )
        assert result.status == PostStatus.PUBLISHED

        # Test: stores correct fields
        mock_db.reset_mock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", "post-new")
        result = post_service.create_post(
            community_id="comm-999",
            author_id="user-111",
            title="Specific Title",
            content="Specific content.",
        )
        assert result.community_id == "comm-999"
        assert result.author_id == "user-111"
        assert result.title == "Specific Title"
        assert result.content == "Specific content."


# ---------------------------------------------------------------------------
# Tests: update_post
# ---------------------------------------------------------------------------


class TestUpdatePost:
    """Tests for PostService.update_post."""

    def test_update_post(self, post_service, mock_db, sample_post):
        """update_post updates fields, persists changes, and handles not-found."""
        # Test: returns updated post
        mock_db.query.return_value.filter.return_value.first.return_value = sample_post
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        result = post_service.update_post("post-123", title="Updated Title")
        assert result is not None
        assert result.id == "post-123"
        assert result.title == "Updated Title"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Test: title-only update preserves content
        mock_db.reset_mock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_post
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        result = post_service.update_post("post-123", title="New Title Only")
        assert result.title == "New Title Only"
        assert result.content == "This is the test post content."

        # Test: content-only update preserves title
        mock_db.reset_mock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_post
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        result = post_service.update_post("post-123", content="New content only")
        assert result.title == "Test Post Title"
        assert result.content == "New content only"

        # Test: status update
        mock_db.reset_mock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_post
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        result = post_service.update_post("post-123", status=PostStatus.ARCHIVED)
        assert result.status == PostStatus.ARCHIVED

        # Test: not found returns None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = post_service.update_post("nonexistent-id", title="Updated Title")
        assert result is None

        # Test: no changes returns post unchanged
        mock_db.reset_mock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_post
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        result = post_service.update_post("post-123")
        assert result is not None
        assert result.title == "Test Post Title"
        assert result.content == "This is the test post content."


# ---------------------------------------------------------------------------
# Tests: delete_post
# ---------------------------------------------------------------------------


class TestDeletePost:
    """Tests for PostService.delete_post."""

    def test_delete_post(self, post_service, mock_db, sample_post):
        """delete_post removes post from DB, returns True on success, False when not found."""
        # Test: successful deletion
        mock_db.query.return_value.filter.return_value.first.return_value = sample_post
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None
        result = post_service.delete_post("post-123")
        assert result is True
        mock_db.delete.assert_called_once_with(sample_post)
        mock_db.commit.assert_called_once()

        # Test: not found returns False
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = post_service.delete_post("nonexistent-id")
        assert result is False

        # Test: not found does not commit
        mock_db.reset_mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        post_service.delete_post("nonexistent-id")
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

        # Test: works with various post ID formats
        post = Post(
            id="post-abc-xyz",
            community_id="comm-456",
            author_id="user-789",
            title="Deletable Post",
            content="Content to delete.",
            status=PostStatus.PUBLISHED,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        mock_db.query.return_value.filter.return_value.first.return_value = post
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None
        result = post_service.delete_post("post-abc-xyz")
        assert result is True
        mock_db.delete.assert_called_once_with(post)
