"""Tests for the Member Service."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.services.member_service import MemberService
from app.models.member import Member, MemberRole, MemberStatus


@pytest.fixture
def mock_db():
    """Provide a mock database session."""
    return MagicMock()


@pytest.fixture
def member_service(mock_db):
    """Provide a MemberService instance with a mock DB."""
    return MemberService(db=mock_db)


@pytest.fixture
def sample_member():
    """Provide a sample member object."""
    return Member(
        id="member-001",
        community_id="comm-001",
        user_id="user-001",
        role=MemberRole.MEMBER,
        status=MemberStatus.ACTIVE,
        joined_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_admin_member():
    """Provide a sample admin member object."""
    return Member(
        id="member-002",
        community_id="comm-001",
        user_id="user-002",
        role=MemberRole.ADMIN,
        status=MemberStatus.ACTIVE,
        joined_at=datetime.now(timezone.utc),
    )


class TestMemberService:
    """Test suite for MemberService."""

    def test_add_member(self, member_service, mock_db):
        """Test adding a new member to a community."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = member_service.add_member(
            community_id="comm-001",
            user_id="user-003",
            role=MemberRole.MEMBER,
        )

        assert result is not None
        assert result.community_id == "comm-001"
        assert result.user_id == "user-003"
        assert result.role == MemberRole.MEMBER
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_add_member_duplicate(self, member_service, mock_db, sample_member):
        """Test adding a member that already exists raises an error."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_member

        with pytest.raises(ValueError, match="already a member"):
            member_service.add_member(
                community_id="comm-001",
                user_id="user-001",
            )

    def test_get_member_by_id_found(self, member_service, mock_db, sample_member):
        """Test retrieving a member by ID when it exists."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_member

        result = member_service.get_member_by_id("member-001")

        assert result is not None
        assert result.id == "member-001"
        assert result.user_id == "user-001"

    def test_get_member_by_id_not_found(self, member_service, mock_db):
        """Test retrieving a member by ID when it does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = member_service.get_member_by_id("nonexistent")

        assert result is None

    def test_get_members_by_community(self, member_service, mock_db, sample_member, sample_admin_member):
        """Test retrieving all members of a community."""
        mock_db.query.return_value.filter.return_value.all.return_value = [
            sample_member,
            sample_admin_member,
        ]

        results = member_service.get_members_by_community("comm-001")

        assert len(results) == 2
        assert all(m.community_id == "comm-001" for m in results)

    def test_get_members_by_community_empty(self, member_service, mock_db):
        """Test retrieving members when community has none."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        results = member_service.get_members_by_community("comm-empty")

        assert results == []

    def test_update_member_role(self, member_service, mock_db, sample_member):
        """Test updating a member's role."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_member
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = member_service.update_member_role(
            member_id="member-001",
            new_role=MemberRole.MODERATOR,
        )

        assert result is not None
        assert result.role == MemberRole.MODERATOR
        mock_db.commit.assert_called_once()

    def test_update_member_role_not_found(self, member_service, mock_db):
        """Test updating role for a member that does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = member_service.update_member_role(
            member_id="nonexistent",
            new_role=MemberRole.MODERATOR,
        )

        assert result is None

    def test_remove_member(self, member_service, mock_db, sample_member):
        """Test removing a member from a community."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_member
        mock_db.delete = MagicMock()
        mock_db.commit = MagicMock()

        result = member_service.remove_member("member-001")

        assert result is True
        mock_db.delete.assert_called_once_with(sample_member)
        mock_db.commit.assert_called_once()

    def test_remove_member_not_found(self, member_service, mock_db):
        """Test removing a member that does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = member_service.remove_member("nonexistent")

        assert result is False

    def test_is_member(self, member_service, mock_db, sample_member):
        """Test checking if a user is a member of a community."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_member

        result = member_service.is_member(community_id="comm-001", user_id="user-001")

        assert result is True

    def test_is_not_member(self, member_service, mock_db):
        """Test checking membership for a non-member."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = member_service.is_member(community_id="comm-001", user_id="user-999")

        assert result is False

    def test_is_admin(self, member_service, mock_db, sample_admin_member):
        """Test checking if a user is an admin of a community."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_admin_member

        result = member_service.is_admin(community_id="comm-001", user_id="user-002")

        assert result is True

    def test_is_not_admin(self, member_service, mock_db, sample_member):
        """Test checking admin status for a non-admin member."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_member

        result = member_service.is_admin(community_id="comm-001", user_id="user-001")

        assert result is False

    def test_deactivate_member(self, member_service, mock_db, sample_member):
        """Test deactivating a member."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_member
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = member_service.deactivate_member("member-001")

        assert result is not None
        assert result.status == MemberStatus.INACTIVE
        mock_db.commit.assert_called_once()

    def test_activate_member(self, member_service, mock_db):
        """Test activating an inactive member."""
        inactive_member = Member(
            id="member-003",
            community_id="comm-001",
            user_id="user-003",
            role=MemberRole.MEMBER,
            status=MemberStatus.INACTIVE,
            joined_at=datetime.now(timezone.utc),
        )
        mock_db.query.return_value.filter.return_value.first.return_value = inactive_member
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = member_service.activate_member("member-003")

        assert result is not None
        assert result.status == MemberStatus.ACTIVE
        mock_db.commit.assert_called_once()
