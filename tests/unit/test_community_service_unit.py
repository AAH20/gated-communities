"""Unit tests for the CommunityService."""

import pytest

from gated_communities.services.community_service import (
    Community,
    CommunityNotFoundError,
    CommunityService,
    CommunityStatus,
    PaginatedResult,
    PaginationParams,
    ValidationError,
)


@pytest.fixture
def community_service():
    """Provide a CommunityService instance backed by its in-memory store."""
    return CommunityService()


@pytest.fixture
def sample_community_data():
    """Provide sample data for creating a community."""
    return {
        "name": "New Community",
        "description": "A newly created community",
    }


class TestCreateCommunity:
    """Tests for CommunityService.create_community."""

    def test_create_community(self, community_service, sample_community_data):
        """Test that a community is created successfully."""
        result = community_service.create_community(sample_community_data)

        assert isinstance(result, Community)
        assert result.id
        assert result.name == sample_community_data["name"]
        assert result.description == sample_community_data["description"]
        assert result.status == CommunityStatus.ACTIVE
        assert result.created_at == result.updated_at

    def test_create_community_persists_to_repository(
        self, community_service, sample_community_data
    ):
        """Test that a created community is retrievable and listed afterwards."""
        created = community_service.create_community(sample_community_data)

        assert community_service.get_community(created.id) is created
        assert community_service.list_communities().total == 1

    def test_create_community_requires_name(self, community_service):
        """A community without a name is rejected."""
        with pytest.raises(ValidationError):
            community_service.create_community({"description": "no name"})

    def test_create_community_requires_description(self, community_service):
        """A community without a description is rejected."""
        with pytest.raises(ValidationError):
            community_service.create_community({"name": "no description"})

    def test_create_community_rejects_unknown_status(
        self, community_service, sample_community_data
    ):
        """An unsupported status value is rejected."""
        with pytest.raises(ValidationError):
            community_service.create_community(
                {**sample_community_data, "status": "not-a-status"}
            )

    def test_create_community_accepts_explicit_status(
        self, community_service, sample_community_data
    ):
        """A valid status value is honoured."""
        result = community_service.create_community(
            {**sample_community_data, "status": CommunityStatus.ARCHIVED.value}
        )
        assert result.status == CommunityStatus.ARCHIVED


class TestGetCommunity:
    """Tests for CommunityService.get_community."""

    def test_get_community(self, community_service, sample_community_data):
        """Test that a community is retrieved successfully by ID."""
        created = community_service.create_community(sample_community_data)

        result = community_service.get_community(created.id)

        assert result is created
        assert result.name == sample_community_data["name"]
        assert result.description == sample_community_data["description"]

    def test_get_community_not_found(self, community_service):
        """Test that get_community raises when the community does not exist."""
        with pytest.raises(CommunityNotFoundError):
            community_service.get_community("nonexistent-id")

    def test_get_community_empty_id_raises(self, community_service):
        """An empty identifier is rejected as a validation error."""
        with pytest.raises(ValidationError):
            community_service.get_community("")


class TestListCommunities:
    """Tests for CommunityService.list_communities."""

    def test_list_communities(self, community_service):
        """Test that all communities are listed successfully."""
        first = community_service.create_community(
            {"name": "Test Community", "description": "First"}
        )
        second = community_service.create_community(
            {"name": "Another Community", "description": "Second"}
        )

        result = community_service.list_communities()

        assert isinstance(result, PaginatedResult)
        assert result.total == 2
        assert {c.id for c in result.items} == {first.id, second.id}

    def test_list_communities_empty(self, community_service):
        """Test that list_communities handles an empty store."""
        result = community_service.list_communities()

        assert result.total == 0
        assert result.items == []

    def test_list_communities_name_filter(self, community_service):
        """The name_contains filter is applied case-insensitively."""
        community_service.create_community({"name": "Alpha Guild", "description": "d"})
        community_service.create_community({"name": "Beta Guild", "description": "d"})

        result = community_service.list_communities(filters={"name_contains": "alpha"})

        assert result.total == 1
        assert result.items[0].name == "Alpha Guild"

    def test_list_communities_pagination(self, community_service):
        """Pagination slices the result set."""
        for i in range(3):
            community_service.create_community({"name": f"Community {i}", "description": "d"})

        result = community_service.list_communities(
            pagination=PaginationParams(page=2, page_size=2)
        )

        assert result.total == 3
        assert len(result.items) == 1
        assert result.page == 2
        assert result.page_size == 2
