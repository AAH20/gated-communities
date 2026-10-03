"""Tests for the Post Service."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.services.post_service import PostService
from app.models.post import Post, PostStatus


@pytest.fixture
def mock_db():
    """Provide a mock database session."""
    return MagicMock()


@pytest.fixture
def post_service(mock_db):
    """Provide a PostService instance with a mock DB."""
    return PostService(db=mock_db)


@pytest.fixture
def sample_post():
    """Provide a sample post object."""
    return Post(
        id="post-001",
        community_id="comm-001",
        author_id="user-001",
        title="Test Post",
        content="This is a test post content.",
        status=PostStatus.PUBLISHED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_draft_post():
    """Provide a sample draft post object."""
    return Post(
        id="post-002",
        community_id="comm-001",
        author_id="user-002",
        title="Draft Post",
        content="This is a draft post.",
        status=PostStatus.DRAFT,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestPostService:
    """Test suite for PostService."""

    def test_create_post(self, post_service, mock_db):
        """Test creating a new post."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = post_service.create_post(
            community_id="comm-001",
            author_id="user-001",
            title="New Post",
            content="Content of the new post.",
        )

        assert result is not None
        assert result.community_id == "comm-001"
        assert result.author_id == "user-001"
        assert result.title == "New Post"
        assert result.content == "Content of the new post."
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_get_post_by_id_found(self, post_service, mock_db, sample_post):
        """Test retrieving a post by ID when it exists."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_post

        result = post_service.get_post_by_id("post-001")

        assert result is not None
        assert result.id == "post-001"
        assert result.title == "Test Post"

    def test_get_post_by_id_not_found(self, post_service, mock_db):
        """Test retrieving a post by ID when it does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = post_service.get_post_by_id("nonexistent")

        assert result is None

    def test_list_posts_by_community(self, post_service, mock_db, sample_post, sample_draft_post):
        """Test listing all posts in a community."""
        mock_db.query.return_value.filter.return_value.all.return_value = [
            sample_post,
            sample_draft_post,
        ]

        results = post_service.list_posts_by_community("comm-001")

        assert len(results) == 2
        assert all(p.community_id == "comm-001" for p in results)

    def test_list_posts_by_community_empty(self, post_service, mock_db):
        """Test listing posts when community has none."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        results = post_service.list_posts_by_community("comm-empty")

        assert results == []

    def test_list_posts_by_author(self, post_service, mock_db, sample_post):
        """Test listing all posts by a specific author."""
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_post]

        results = post_service.list_posts_by_author("user-001")

        assert len(results) == 1
        assert results[0].author_id == "user-001"

    def test_update_post(self, post_service, mock_db, sample_post):
        """Test updating an existing post."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_post
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = post_service.update_post(
            post_id="post-001",
            title="Updated Title",
            content="Updated content.",
        )

        assert result is not None
        assert result.title == "Updated Title"
        assert result.content == "Updated content."
        mock_db.commit.assert_called_once()

    def test_update_post_not_found(self, post_service, mock_db):
        """Test updating a post that does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = post_service.update_post(
            post_id="nonexistent",
            title="Updated",
        )

        assert result is None

    def test_delete_post(self, post_service, mock_db, sample_post):
        """Test deleting a post."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_post
        mock_db.delete = MagicMock()
        mock_db.commit = MagicMock()

        result = post_service.delete_post("post-001")

        assert result is True
        mock_db.delete.assert_called_once_with(sample_post)
        mock_db.commit.assert_called_once()

    def test_delete_post_not_found(self, post_service, mock_db):
        """Test deleting a post that does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = post_service.delete_post("nonexistent")

        assert result is False

    def test_publish_post(self, post_service, mock_db, sample_draft_post):
        """Test publishing a draft post."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_draft_post
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = post_service.publish_post("post-002")

        assert result is not None
        assert result.status == PostStatus.PUBLISHED
        mock_db.commit.assert_called_once()

    def test_publish_post_not_found(self, post_service, mock_db):
        """Test publishing a post that does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = post_service.publish_post("nonexistent")

        assert result is None

    def test_archive_post(self, post_service, mock_db, sample_post):
        """Test archiving a published post."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_post
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = post_service.archive_post("post-001")

        assert result is not None
        assert result.status == PostStatus.ARCHIVED
        mock_db.commit.assert_called_once()

    def test_archive_post_not_found(self, post_service, mock_db):
        """Test archiving a post that does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = post_service.archive_post("nonexistent")

        assert result is None

    def test_search_posts(self, post_service, mock_db, sample_post):
        """Test searching posts by title or content."""
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_post]

        results = post_service.search_posts(query="Test")

        assert len(results) == 1
        assert results[0].title == "Test Post"

    def test_search_posts_no_results(self, post_service, mock_db):
        """Test searching posts with no matching results."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        results = post_service.search_posts(query="NonexistentQuery")

        assert results == []

    def test_get_posts_count_by_community(self, post_service, mock_db):
        """Test getting the post count for a community."""
        mock_db.query.return_value.filter.return_value.count.return_value = 15

        count = post_service.get_posts_count_by_community("comm-001")

        assert count == 15
