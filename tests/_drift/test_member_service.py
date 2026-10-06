"""Comprehensive service tests for MemberService."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from gated_communities.services.member_service import MemberService
from gated_communities.member import Member, MemberStatus, MemberRole
from gated_communities.exceptions import (
    MemberNotFoundError,
    DuplicateMemberError,
    InvalidMemberDataError,
    CommunityNotFoundError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Provide a mock database session."""
    db = MagicMock()
    db.query.return_value = db
    db.filter.return_value = db
    db.first.return_value = None
    db.all.return_value = []
    db.add.return_value = None
    db.commit.return_value = None
    db.delete.return_value = None
    return db


@pytest.fixture
def member_service(mock_db):
    """Provide a MemberService instance with a mocked database."""
    return MemberService(db=mock_db)


@pytest.fixture
def sample_member():
    """Provide a sample Member instance."""
    return Member(
        id=1,
        community_id=10,
        user_id=100,
        role=MemberRole.MEMBER,
        status=MemberStatus.ACTIVE,
        display_name="Test User",
        joined_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_member_dict():
    """Provide a sample member data dictionary for creation."""
    return {
        "community_id": 10,
        "user_id": 100,
        "role": MemberRole.MEMBER,
        "status": MemberStatus.ACTIVE,
        "display_name": "Test User",
    }


@pytest.fixture
def multiple_members():
    """Provide a list of multiple Member instances."""
    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [
        Member(
            id=i,
            community_id=10,
            user_id=100 + i,
            role=MemberRole.MEMBER,
            status=MemberStatus.ACTIVE,
            display_name=f"User {i}",
            joined_at=base_time + timedelta(days=i),
            created_at=base_time + timedelta(days=i),
            updated_at=base_time + timedelta(days=i),
        )
        for i in range(1, 6)
    ]


# ---------------------------------------------------------------------------
# Tests: get_member
# ---------------------------------------------------------------------------


class TestGetMember:
    """Tests for MemberService.get_member."""

    def test_get_member_returns_member_when_found(
        self, member_service, mock_db, sample_member
    ):
        """get_member should return the member when it exists."""
        mock_db.first.return_value = sample_member

        result = member_service.get_member(member_id=1)

        assert result is not None
        assert result.id == 1
        assert result.community_id == 10
        assert result.user_id == 100
        assert result.display_name == "Test User"

    def test_get_member_raises_not_found_when_missing(self, member_service, mock_db):
        """get_member should raise MemberNotFoundError when member does not exist."""
        mock_db.first.return_value = None

        with pytest.raises(MemberNotFoundError):
            member_service.get_member(member_id=999)

    def test_get_member_queries_correct_id(self, member_service, mock_db, sample_member):
        """get_member should query using the provided member_id."""
        mock_db.first.return_value = sample_member

        member_service.get_member(member_id=42)

        mock_db.filter.assert_called()
        assert mock_db.query.called

    def test_get_member_with_invalid_id_raises_error(self, member_service):
        """get_member should raise InvalidMemberDataError for invalid id."""
        with pytest.raises(InvalidMemberDataError):
            member_service.get_member(member_id=-1)

    def test_get_member_with_zero_id_raises_error(self, member_service):
        """get_member should raise InvalidMemberDataError for zero id."""
        with pytest.raises(InvalidMemberDataError):
            member_service.get_member(member_id=0)

    def test_get_member_with_none_id_raises_error(self, member_service):
        """get_member should raise InvalidMemberDataError for None id."""
        with pytest.raises(InvalidMemberDataError):
            member_service.get_member(member_id=None)


# ---------------------------------------------------------------------------
# Tests: list_members
# ---------------------------------------------------------------------------


class TestListMembers:
    """Tests for MemberService.list_members."""

    def test_list_members_returns_all_when_no_filters(
        self, member_service, mock_db, multiple_members
    ):
        """list_members should return all members when no filters are applied."""
        mock_db.all.return_value = multiple_members

        result = member_service.list_members(community_id=10)

        assert len(result) == 5
        assert all(isinstance(m, Member) for m in result)

    def test_list_members_filters_by_community_id(
        self, member_service, mock_db, multiple_members
    ):
        """list_members should filter by community_id."""
        mock_db.all.return_value = multiple_members

        result = member_service.list_members(community_id=10)

        assert len(result) == 5
        assert all(m.community_id == 10 for m in result)

    def test_list_members_filters_by_status(
        self, member_service, mock_db, multiple_members
    ):
        """list_members should filter by status."""
        for m in multiple_members:
            m.status = MemberStatus.ACTIVE
        mock_db.all.return_value = multiple_members

        result = member_service.list_members(
            community_id=10, status=MemberStatus.ACTIVE
        )

        assert len(result) == 5
        assert all(m.status == MemberStatus.ACTIVE for m in result)

    def test_list_members_filters_by_role(
        self, member_service, mock_db, multiple_members
    ):
        """list_members should filter by role."""
        for m in multiple_members:
            m.role = MemberRole.MODERATOR
        mock_db.all.return_value = multiple_members

        result = member_service.list_members(
            community_id=10, role=MemberRole.MODERATOR
        )

        assert len(result) == 5
        assert all(m.role == MemberRole.MODERATOR for m in result)

    def test_list_members_with_pagination_limit(
        self, member_service, mock_db, multiple_members
    ):
        """list_members should respect the limit parameter."""
        mock_db.all.return_value = multiple_members[:2]

        result = member_service.list_members(community_id=10, limit=2)

        assert len(result) == 2

    def test_list_members_with_pagination_offset(
        self, member_service, mock_db, multiple_members
    ):
        """list_members should respect the offset parameter."""
        mock_db.all.return_value = multiple_members[2:]

        result = member_service.list_members(community_id=10, offset=2)

        assert len(result) == 3

    def test_list_members_returns_empty_list_when_no_matches(self, member_service, mock_db):
        """list_members should return empty list when no members match."""
        mock_db.all.return_value = []

        result = member_service.list_members(community_id=999)

        assert result == []

    def test_list_members_with_multiple_filters(
        self, member_service, mock_db, multiple_members
    ):
        """list_members should apply multiple filters simultaneously."""
        for m in multiple_members:
            m.status = MemberStatus.ACTIVE
            m.role = MemberRole.ADMIN
        mock_db.all.return_value = multiple_members[:3]

        result = member_service.list_members(
            community_id=10,
            status=MemberStatus.ACTIVE,
            role=MemberRole.ADMIN,
            limit=10,
            offset=0,
        )

        assert len(result) == 3
        assert all(m.status == MemberStatus.ACTIVE for m in result)
        assert all(m.role == MemberRole.ADMIN for m in result)

    def test_list_members_orders_by_joined_at_descending(
        self, member_service, mock_db, multiple_members
    ):
        """list_members should order results by joined_at descending by default."""
        mock_db.all.return_value = sorted(
            multiple_members, key=lambda m: m.joined_at, reverse=True
        )

        result = member_service.list_members(community_id=10)

        for i in range(len(result) - 1):
            assert result[i].joined_at >= result[i + 1].joined_at


# ---------------------------------------------------------------------------
# Tests: create_member
# ---------------------------------------------------------------------------


class TestCreateMember:
    """Tests for MemberService.create_member."""

    def test_create_member_success(
        self, member_service, mock_db, sample_member_dict, sample_member
    ):
        """create_member should create and return a new member."""
        mock_db.add.side_effect = lambda obj: setattr(obj, "id", 1)

        result = member_service.create_member(**sample_member_dict)

        assert result is not None
        assert result.community_id == 10
        assert result.user_id == 100
        assert result.display_name == "Test User"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_member_with_minimal_data(self, member_service, mock_db):
        """create_member should work with minimal required data."""
        mock_db.add.side_effect = lambda obj: setattr(obj, "id", 1)

        result = member_service.create_member(
            community_id=10, user_id=100
        )

        assert result is not None
        assert result.community_id == 10
        assert result.user_id == 100

    def test_create_member_raises_on_duplicate(
        self, member_service, mock_db, sample_member_dict
    ):
        """create_member should raise DuplicateMemberError for duplicate entries."""
        mock_db.add.side_effect = Exception("UNIQUE constraint failed")

        with pytest.raises(DuplicateMemberError):
            member_service.create_member(**sample_member_dict)

    def test_create_member_raises_on_invalid_community(self, member_service):
        """create_member should raise InvalidMemberDataError for invalid community_id."""
        with pytest.raises(InvalidMemberDataError):
            member_service.create_member(community_id=-1, user_id=100)

    def test_create_member_raises_on_invalid_user(self, member_service):
        """create_member should raise InvalidMemberDataError for invalid user_id."""
        with pytest.raises(InvalidMemberDataError):
            member_service.create_member(community_id=10, user_id=-1)

    def test_create_member_raises_on_missing_community_id(self, member_service):
        """create_member should raise InvalidMemberDataError when community_id is missing."""
        with pytest.raises(InvalidMemberDataError):
            member_service.create_member(user_id=100)

    def test_create_member_raises_on_missing_user_id(self, member_service):
        """create_member should raise InvalidMemberDataError when user_id is missing."""
        with pytest.raises(InvalidMemberDataError):
            member_service.create_member(community_id=10)

    def test_create_member_sets_default_role(self, member_service, mock_db):
        """create_member should set default role to MEMBER."""
        mock_db.add.side_effect = lambda obj: setattr(obj, "id", 1)

        result = member_service.create_member(community_id=10, user_id=100)

        assert result.role == MemberRole.MEMBER

    def test_create_member_sets_default_status(self, member_service, mock_db):
        """create_member should set default status to ACTIVE."""
        mock_db.add.side_effect = lambda obj: setattr(obj, "id", 1)

        result = member_service.create_member(community_id=10, user_id=100)

        assert result.status == MemberStatus.ACTIVE

    def test_create_member_with_custom_role(self, member_service, mock_db):
        """create_member should accept a custom role."""
        mock_db.add.side_effect = lambda obj: setattr(obj, "id", 1)

        result = member_service.create_member(
            community_id=10, user_id=100, role=MemberRole.ADMIN
        )

        assert result.role == MemberRole.ADMIN

    def test_create_member_with_custom_status(self, member_service, mock_db):
        """create_member should accept a custom status."""
        mock_db.add.side_effect = lambda obj: setattr(obj, "id", 1)

        result = member_service.create_member(
            community_id=10, user_id=100, status=MemberStatus.PENDING
        )

        assert result.status == MemberStatus.PENDING

    def test_create_member_commits_to_database(self, member_service, mock_db):
        """create_member should commit the transaction."""
        mock_db.add.side_effect = lambda obj: setattr(obj, "id", 1)

        member_service.create_member(community_id=10, user_id=100)

        mock_db.commit.assert_called_once()

    def test_create_member_adds_to_session(self, member_service, mock_db):
        """create_member should add the new member to the database session."""
        mock_db.add.side_effect = lambda obj: setattr(obj, "id", 1)

        member_service.create_member(community_id=10, user_id=100)

        mock_db.add.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: update_member
# ---------------------------------------------------------------------------


class TestUpdateMember:
    """Tests for MemberService.update_member."""

    def test_update_member_success(
        self, member_service, mock_db, sample_member
    ):
        """update_member should update and return the member."""
        mock_db.first.return_value = sample_member

        result = member_service.update_member(
            member_id=1, display_name="Updated Name"
        )

        assert result is not None
        assert result.display_name == "Updated Name"
        mock_db.commit.assert_called_once()

    def test_update_member_role(self, member_service, mock_db, sample_member):
        """update_member should update the member role."""
        mock_db.first.return_value = sample_member

        result = member_service.update_member(
            member_id=1, role=MemberRole.MODERATOR
        )

        assert result.role == MemberRole.MODERATOR

    def test_update_member_status(self, member_service, mock_db, sample_member):
        """update_member should update the member status."""
        mock_db.first.return_value = sample_member

        result = member_service.update_member(
            member_id=1, status=MemberStatus.SUSPENDED
        )

        assert result.status == MemberStatus.SUSPENDED

    def test_update_member_display_name(self, member_service, mock_db, sample_member):
        """update_member should update the display name."""
        mock_db.first.return_value = sample_member

        result = member_service.update_member(
            member_id=1, display_name="New Display Name"
        )

        assert result.display_name == "New Display Name"

    def test_update_member_raises_not_found(self, member_service, mock_db):
        """update_member should raise MemberNotFoundError when member does not exist."""
        mock_db.first.return_value = None

        with pytest.raises(MemberNotFoundError):
            member_service.update_member(member_id=999, display_name="New Name")

    def test_update_member_with_invalid_id_raises_error(self, member_service):
        """update_member should raise InvalidMemberDataError for invalid id."""
        with pytest.raises(InvalidMemberDataError):
            member_service.update_member(member_id=-1, display_name="New Name")

    def test_update_member_with_no_changes(
        self, member_service, mock_db, sample_member
    ):
        """update_member should handle update with no field changes."""
        mock_db.first.return_value = sample_member

        result = member_service.update_member(member_id=1)

        assert result is not None
        assert result.id == 1

    def test_update_member_updates_updated_at_timestamp(
        self, member_service, mock_db, sample_member
    ):
        """update_member should update the updated_at timestamp."""
        mock_db.first.return_value = sample_member
        original_updated_at = sample_member.updated_at

        result = member_service.update_member(
            member_id=1, display_name="Updated"
        )

        assert result.updated_at >= original_updated_at

    def test_update_member_multiple_fields(
        self, member_service, mock_db, sample_member
    ):
        """update_member should update multiple fields at once."""
        mock_db.first.return_value = sample_member

        result = member_service.update_member(
            member_id=1,
            display_name="Multi Update",
            role=MemberRole.ADMIN,
            status=MemberStatus.ACTIVE,
        )

        assert result.display_name == "Multi Update"
        assert result.role == MemberRole.ADMIN
        assert result.status == MemberStatus.ACTIVE

    def test_update_member_commits_to_database(
        self, member_service, mock_db, sample_member
    ):
        """update_member should commit the transaction."""
        mock_db.first.return_value = sample_member

        member_service.update_member(member_id=1, display_name="Updated")

        mock_db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: delete_member
# ---------------------------------------------------------------------------


class TestDeleteMember:
    """Tests for MemberService.delete_member."""

    def test_delete_member_success(self, member_service, mock_db, sample_member):
        """delete_member should delete an existing member."""
        mock_db.first.return_value = sample_member

        member_service.delete_member(member_id=1)

        mock_db.delete.assert_called_once_with(sample_member)
        mock_db.commit.assert_called_once()

    def test_delete_member_raises_not_found(self, member_service, mock_db):
        """delete_member should raise MemberNotFoundError when member does not exist."""
        mock_db.first.return_value = None

        with pytest.raises(MemberNotFoundError):
            member_service.delete_member(member_id=999)

    def test_delete_member_with_invalid_id_raises_error(self, member_service):
        """delete_member should raise InvalidMemberDataError for invalid id."""
        with pytest.raises(InvalidMemberDataError):
            member_service.delete_member(member_id=-1)

    def test_delete_member_with_zero_id_raises_error(self, member_service):
        """delete_member should raise InvalidMemberDataError for zero id."""
        with pytest.raises(InvalidMemberDataError):
            member_service.delete_member(member_id=0)

    def test_delete_member_with_none_id_raises_error(self, member_service):
        """delete_member should raise InvalidMemberDataError for None id."""
        with pytest.raises(InvalidMemberDataError):
            member_service.delete_member(member_id=None)

    def test_delete_member_commits_to_database(
        self, member_service, mock_db, sample_member
    ):
        """delete_member should commit the transaction."""
        mock_db.first.return_value = sample_member

        member_service.delete_member(member_id=1)

        mock_db.commit.assert_called_once()

    def test_delete_member_calls_db_delete(
        self, member_service, mock_db, sample_member
    ):
        """delete_member should call db.delete with the correct member."""
        mock_db.first.return_value = sample_member

        member_service.delete_member(member_id=1)

        mock_db.delete.assert_called_once_with(sample_member)

    def test_delete_member_returns_none_on_success(
        self, member_service, mock_db, sample_member
    ):
        """delete_member should return None on successful deletion."""
        mock_db.first.return_value = sample_member

        result = member_service.delete_member(member_id=1)

        assert result is None
