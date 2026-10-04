"""Comprehensive service tests for community operations."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from gated_communities.services.community_service import (
    get_community,
    list_communities,
    create_community,
    update_community,
    delete_community,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Provide a mock database session."""
    return MagicMock()


@pytest.fixture
def sample_community():
    """Return a sample community dict."""
    return {
        "id": "comm-001",
        "name": "Test Community",
        "description": "A test community for unit testing",
        "slug": "test-community",
        "is_active": True,
        "is_private": False,
        "member_count": 42,
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 15, tzinfo=timezone.utc),
    }


@pytest.fixture
def sample_community_create():
    """Return data for creating a community."""
    return {
        "name": "New Community",
        "description": "A newly created community",
        "slug": "new-community",
        "is_private": True,
    }


@pytest.fixture
def sample_community_update():
    """Return data for updating a community."""
    return {
        "name": "Updated Community",
        "description": "An updated description",
        "is_active": False,
    }


# ---------------------------------------------------------------------------
# Tests: get_community
# ---------------------------------------------------------------------------


class TestGetCommunity:
    """Tests for get_community service function."""

    def test_get_community_returns_community(self, mock_db, sample_community):
        """get_community returns the community when found."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community

        result = get_community(mock_db, "comm-001")

        assert result is not None
        assert result["id"] == "comm-001"
        assert result["name"] == "Test Community"
        assert result["slug"] == "test-community"
        assert result["is_active"] is True
        assert result["member_count"] == 42

    def test_get_community_not_found_returns_none(self, mock_db):
        """get_community returns None when community does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_community(mock_db, "nonexistent-id")

        assert result is None

    def test_get_community_queries_correct_id(self, mock_db, sample_community):
        """get_community queries with the correct community ID."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community

        get_community(mock_db, "comm-001")

        mock_db.query.assert_called_once()
        mock_db.query.return_value.filter.assert_called_once()

    def test_get_community_with_string_id(self, mock_db, sample_community):
        """get_community works with string IDs."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community

        result = get_community(mock_db, "comm-001")

        assert result["id"] == "comm-001"

    def test_get_community_with_uuid(self, mock_db):
        """get_community works with UUID-style IDs."""
        uuid_community = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "UUID Community",
            "description": "Community with UUID",
            "slug": "uuid-community",
            "is_active": True,
            "is_private": False,
            "member_count": 0,
            "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
        }
        mock_db.query.return_value.filter.return_value.first.return_value = uuid_community

        result = get_community(mock_db, "550e8400-e29b-41d4-a716-446655440000")

        assert result is not None
        assert result["id"] == "550e8400-e29b-41d4-a716-446655440000"

    def test_get_community_preserves_all_fields(self, mock_db, sample_community):
        """get_community preserves all community fields."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community

        result = get_community(mock_db, "comm-001")

        assert result["name"] == "Test Community"
        assert result["description"] == "A test community for unit testing"
        assert result["slug"] == "test-community"
        assert result["is_active"] is True
        assert result["is_private"] is False
        assert result["member_count"] == 42
        assert result["created_at"] == datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert result["updated_at"] == datetime(2024, 1, 15, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Tests: list_communities
# ---------------------------------------------------------------------------


class TestListCommunities:
    """Tests for list_communities service function."""

    def test_list_communities_returns_all(self, mock_db, sample_community):
        """list_communities returns all communities when no filter."""
        communities = [
            sample_community,
            {**sample_community, "id": "comm-002", "name": "Second Community"},
        ]
        mock_db.query.return_value.all.return_value = communities

        result = list_communities(mock_db)

        assert len(result) == 2
        assert result[0]["id"] == "comm-001"
        assert result[1]["id"] == "comm-002"

    def test_list_communities_empty_result(self, mock_db):
        """list_communities returns empty list when no communities exist."""
        mock_db.query.return_value.all.return_value = []

        result = list_communities(mock_db)

        assert result == []

    def test_list_communities_with_pagination(self, mock_db, sample_community):
        """list_communities supports pagination via limit and offset."""
        communities = [sample_community] * 5
        mock_db.query.return_value.limit.return_value.offset.return_value.all.return_value = communities

        result = list_communities(mock_db, limit=5, offset=0)

        assert len(result) == 5
        mock_db.query.return_value.limit.assert_called_once_with(5)
        mock_db.query.return_value.limit.return_value.offset.assert_called_once_with(0)

    def test_list_communities_with_name_filter(self, mock_db, sample_community):
        """list_communities filters by name."""
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_community]

        result = list_communities(mock_db, name="Test")

        assert len(result) == 1
        assert result[0]["name"] == "Test Community"
        mock_db.query.return_value.filter.assert_called_once()

    def test_list_communities_with_active_filter(self, mock_db, sample_community):
        """list_communities filters by active status."""
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_community]

        result = list_communities(mock_db, is_active=True)

        assert len(result) == 1
        assert result[0]["is_active"] is True

    def test_list_communities_with_private_filter(self, mock_db):
        """list_communities filters by private status."""
        private_community = {
            "id": "comm-003",
            "name": "Private Community",
            "description": "A private community",
            "slug": "private-community",
            "is_active": True,
            "is_private": True,
            "member_count": 10,
            "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
        }
        mock_db.query.return_value.filter.return_value.all.return_value = [private_community]

        result = list_communities(mock_db, is_private=True)

        assert len(result) == 1
        assert result[0]["is_private"] is True

    def test_list_communities_with_multiple_filters(self, mock_db, sample_community):
        """list_communities supports multiple filters simultaneously."""
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_community]

        result = list_communities(mock_db, name="Test", is_active=True, is_private=False)

        assert len(result) == 1
        assert result[0]["name"] == "Test Community"
        assert result[0]["is_active"] is True
        assert result[0]["is_private"] is False

    def test_list_communities_with_slug_filter(self, mock_db, sample_community):
        """list_communities filters by slug."""
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_community]

        result = list_communities(mock_db, slug="test-community")

        assert len(result) == 1
        assert result[0]["slug"] == "test-community"

    def test_list_communities_ordering(self, mock_db, sample_community):
        """list_communities supports ordering."""
        communities = [
            sample_community,
            {**sample_community, "id": "comm-002", "name": "Alpha Community"},
        ]
        mock_db.query.return_value.order_by.return_value.all.return_value = communities

        result = list_communities(mock_db, order_by="name")

        assert len(result) == 2
        mock_db.query.return_value.order_by.assert_called_once()

    def test_list_communities_with_limit_only(self, mock_db, sample_community):
        """list_communities supports limit without offset."""
        mock_db.query.return_value.limit.return_value.all.return_value = [sample_community]

        result = list_communities(mock_db, limit=10)

        assert len(result) == 1
        mock_db.query.return_value.limit.assert_called_once_with(10)


# ---------------------------------------------------------------------------
# Tests: create_community
# ---------------------------------------------------------------------------


class TestCreateCommunity:
    """Tests for create_community service function."""

    def test_create_community_success(self, mock_db, sample_community_create):
        """create_community creates and returns a new community."""
        created_community = {
            "id": "comm-new-001",
            **sample_community_create,
            "is_active": True,
            "member_count": 0,
            "created_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
        }
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: obj.__dict__.update(created_community)

        result = create_community(mock_db, sample_community_create)

        assert result is not None
        assert result["id"] == "comm-new-001"
        assert result["name"] == "New Community"
        assert result["description"] == "A newly created community"
        assert result["slug"] == "new-community"
        assert result["is_private"] is True
        assert result["is_active"] is True
        assert result["member_count"] == 0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_community_with_minimal_data(self, mock_db):
        """create_community works with minimal required data."""
        minimal_data = {"name": "Minimal", "slug": "minimal"}
        created_community = {
            "id": "comm-min-001",
            "name": "Minimal",
            "slug": "minimal",
            "description": None,
            "is_active": True,
            "is_private": False,
            "member_count": 0,
            "created_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
        }
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: obj.__dict__.update(created_community)

        result = create_community(mock_db, minimal_data)

        assert result is not None
        assert result["name"] == "Minimal"
        assert result["slug"] == "minimal"
        assert result["is_active"] is True
        assert result["is_private"] is False

    def test_create_community_generates_slug_if_missing(self, mock_db):
        """create_community generates a slug from name if not provided."""
        data_without_slug = {"name": "My New Community", "description": "Test"}
        created_community = {
            "id": "comm-slug-001",
            "name": "My New Community",
            "slug": "my-new-community",
            "description": "Test",
            "is_active": True,
            "is_private": False,
            "member_count": 0,
            "created_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
        }
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: obj.__dict__.update(created_community)

        result = create_community(mock_db, data_without_slug)

        assert result is not None
        assert result["slug"] == "my-new-community"

    def test_create_community_sets_default_is_active(self, mock_db):
        """create_community sets is_active to True by default."""
        data = {"name": "Default Active", "slug": "default-active"}
        created_community = {
            "id": "comm-default-001",
            "name": "Default Active",
            "slug": "default-active",
            "description": None,
            "is_active": True,
            "is_private": False,
            "member_count": 0,
            "created_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
        }
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: obj.__dict__.update(created_community)

        result = create_community(mock_db, data)

        assert result["is_active"] is True

    def test_create_community_sets_default_member_count(self, mock_db):
        """create_community initializes member_count to 0."""
        data = {"name": "Zero Members", "slug": "zero-members"}
        created_community = {
            "id": "comm-zero-001",
            "name": "Zero Members",
            "slug": "zero-members",
            "description": None,
            "is_active": True,
            "is_private": False,
            "member_count": 0,
            "created_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
        }
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: obj.__dict__.update(created_community)

        result = create_community(mock_db, data)

        assert result["member_count"] == 0

    def test_create_community_with_private_flag(self, mock_db):
        """create_community respects the is_private flag."""
        data = {"name": "Secret Community", "slug": "secret-community", "is_private": True}
        created_community = {
            "id": "comm-secret-001",
            "name": "Secret Community",
            "slug": "secret-community",
            "description": None,
            "is_active": True,
            "is_private": True,
            "member_count": 0,
            "created_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
        }
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: obj.__dict__.update(created_community)

        result = create_community(mock_db, data)

        assert result["is_private"] is True

    def test_create_community_commits_to_database(self, mock_db, sample_community_create):
        """create_community commits the transaction."""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: obj.__dict__.update({
            "id": "comm-commit-001",
            **sample_community_create,
            "is_active": True,
            "member_count": 0,
            "created_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
        })

        create_community(mock_db, sample_community_create)

        mock_db.commit.assert_called_once()

    def test_create_community_refreshes_object(self, mock_db, sample_community_create):
        """create_community refreshes the object to get DB-generated values."""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: obj.__dict__.update({
            "id": "comm-refresh-001",
            **sample_community_create,
            "is_active": True,
            "member_count": 0,
            "created_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
        })

        create_community(mock_db, sample_community_create)

        mock_db.refresh.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: update_community
# ---------------------------------------------------------------------------


class TestUpdateCommunity:
    """Tests for update_community service function."""

    def test_update_community_success(self, mock_db, sample_community, sample_community_update):
        """update_community updates and returns the community."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = update_community(mock_db, "comm-001", sample_community_update)

        assert result is not None
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_community_partial_update(self, mock_db, sample_community):
        """update_community supports partial updates."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        partial_update = {"name": "Only Name Changed"}
        result = update_community(mock_db, "comm-001", partial_update)

        assert result is not None
        mock_db.commit.assert_called_once()

    def test_update_community_not_found(self, mock_db):
        """update_community raises or returns None when community not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = update_community(mock_db, "nonexistent-id", {"name": "New Name"})

        assert result is None

    def test_update_community_name(self, mock_db, sample_community):
        """update_community can update the name field."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = update_community(mock_db, "comm-001", {"name": "Renamed Community"})

        assert result is not None
        mock_db.commit.assert_called_once()

    def test_update_community_description(self, mock_db, sample_community):
        """update_community can update the description field."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = update_community(mock_db, "comm-001", {"description": "Updated description"})

        assert result is not None
        mock_db.commit.assert_called_once()

    def test_update_community_active_status(self, mock_db, sample_community):
        """update_community can toggle active status."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = update_community(mock_db, "comm-001", {"is_active": False})

        assert result is not None
        mock_db.commit.assert_called_once()

    def test_update_community_private_status(self, mock_db, sample_community):
        """update_community can toggle private status."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = update_community(mock_db, "comm-001", {"is_private": True})

        assert result is not None
        mock_db.commit.assert_called_once()

    def test_update_community_multiple_fields(self, mock_db, sample_community):
        """update_community can update multiple fields at once."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        multi_update = {
            "name": "Multi Update",
            "description": "Updated description",
            "is_active": False,
            "is_private": True,
        }
        result = update_community(mock_db, "comm-001", multi_update)

        assert result is not None
        mock_db.commit.assert_called_once()

    def test_update_community_with_empty_dict(self, mock_db, sample_community):
        """update_community with empty dict still commits (no-op update)."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = update_community(mock_db, "comm-001", {})

        assert result is not None
        mock_db.commit.assert_called_once()

    def test_update_community_queries_correct_id(self, mock_db, sample_community):
        """update_community queries with the correct community ID."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        update_community(mock_db, "comm-001", {"name": "Test"})

        mock_db.query.assert_called_once()
        mock_db.query.return_value.filter.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: delete_community
# ---------------------------------------------------------------------------


class TestDeleteCommunity:
    """Tests for delete_community service function."""

    def test_delete_community_success(self, mock_db, sample_community):
        """delete_community removes the community and returns True."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        result = delete_community(mock_db, "comm-001")

        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_delete_community_not_found(self, mock_db):
        """delete_community returns False when community does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = delete_community(mock_db, "nonexistent-id")

        assert result is False
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_delete_community_queries_correct_id(self, mock_db, sample_community):
        """delete_community queries with the correct community ID."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        delete_community(mock_db, "comm-001")

        mock_db.query.assert_called_once()
        mock_db.query.return_value.filter.assert_called_once()

    def test_delete_community_commits_transaction(self, mock_db, sample_community):
        """delete_community commits the deletion transaction."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        delete_community(mock_db, "comm-001")

        mock_db.commit.assert_called_once()

    def test_delete_community_calls_delete_on_object(self, mock_db, sample_community):
        """delete_community calls delete on the found community object."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        delete_community(mock_db, "comm-001")

        mock_db.delete.assert_called_once_with(sample_community)

    def test_delete_community_with_uuid(self, mock_db):
        """delete_community works with UUID-style IDs."""
        uuid_community = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "UUID Community",
            "description": "Community with UUID",
            "slug": "uuid-community",
            "is_active": True,
            "is_private": False,
            "member_count": 0,
            "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
        }
        mock_db.query.return_value.filter.return_value.first.return_value = uuid_community
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        result = delete_community(mock_db, "550e8400-e29b-41d4-a716-446655440000")

        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_delete_community_returns_true_on_success(self, mock_db, sample_community):
        """delete_community returns True on successful deletion."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_community
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        result = delete_community(mock_db, "comm-001")

        assert result is True
        assert isinstance(result, bool)

    def test_delete_community_returns_false_on_not_found(self, mock_db):
        """delete_community returns False when community is not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = delete_community(mock_db, "missing-id")

        assert result is False
        assert isinstance(result, bool)
