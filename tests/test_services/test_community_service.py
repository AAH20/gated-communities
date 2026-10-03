"""Tests for the Community Service."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.community_service import CommunityService
from app.models.community import Community, CommunityStatus


@pytest.fixture
def mock_db():
    """Provide a mock database session."""
    return MagicMock()


@pytest.fixture
def community_service(mock_db):
    """Provide a CommunityService instance with a mock DB."""
    return CommunityService(db=mock_db)


@pytest.fixture
def sample_community():
    """Provide a sample community object."""
    return Community(
        id="comm-001",
        name="Test Community",
        description="A test community for unit testing",
        status=CommunityStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestCommunityService:
    """Test suite for CommunityService."""

    def test_create_community(self, community_service, mock_db):
        """Test creating a new community."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = community_service.create_community(
            name="New Community",
            description="A newly created community",
        )

        assert result is not None
        assert result.name == "New Community"
        assert result.description == "A newly created community"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_get_community_by_id_found(self, community_service, mock_db, sample_community):
        """Test retrieving a community by ID when it exists."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community

        result = community_service.get_community_by_id("comm-001")

        assert result is not None
        assert result.id == "comm-001"
        assert result.name == "Test Community"

    def test_get_community_by_id_not_found(self, community_service, mock_db):
        """Test retrieving a community by ID when it does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = community_service.get_community_by_id("nonexistent")

        assert result is None

    def test_list_communities(self, community_service, mock_db, sample_community):
        """Test listing all communities."""
        mock_db.query.return_value.all.return_value = [sample_community]

        results = community_service.list_communities()

        assert len(results) == 1
        assert results[0].id == "comm-001"

    def test_list_communities_empty(self, community_service, mock_db):
        """Test listing communities when none exist."""
        mock_db.query.return_value.all.return_value = []

        results = community_service.list_communities()

        assert results == []

    def test_update_community(self, community_service, mock_db, sample_community):
        """Test updating an existing community."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = community_service.update_community(
            community_id="comm-001",
            name="Updated Community",
            description="Updated description",
        )

        assert result is not None
        assert result.name == "Updated Community"
        assert result.description == "Updated description"
        mock_db.commit.assert_called_once()

    def test_update_community_not_found(self, community_service, mock_db):
        """Test updating a community that does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = community_service.update_community(
            community_id="nonexistent",
            name="Updated",
        )

        assert result is None

    def test_delete_community(self, community_service, mock_db, sample_community):
        """Test deleting a community."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.delete = MagicMock()
        mock_db.commit = MagicMock()

        result = community_service.delete_community("comm-001")

        assert result is True
        mock_db.delete.assert_called_once_with(sample_community)
        mock_db.commit.assert_called_once()

    def test_delete_community_not_found(self, community_service, mock_db):
        """Test deleting a community that does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = community_service.delete_community("nonexistent")

        assert result is False

    def test_search_communities(self, community_service, mock_db, sample_community):
        """Test searching communities by name."""
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_community]

        results = community_service.search_communities(query="Test")

        assert len(results) == 1
        assert results[0].name == "Test Community"

    def test_get_community_members_count(self, community_service, mock_db):
        """Test getting the member count for a community."""
        mock_db.query.return_value.filter.return_value.count.return_value = 42

        count = community_service.get_community_members_count("comm-001")

        assert count == 42
