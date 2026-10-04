"""Integration tests for member workflow in gated-communities."""

import pytest
from unittest.mock import MagicMock, patch
from gated_communities import MemberService, Member, AccessLevel


@pytest.fixture
def member_service():
    """Fixture providing a MemberService instance with mocked dependencies."""
    service = MemberService()
    service.repository = MagicMock()
    service.notification_service = MagicMock()
    return service


@pytest.fixture
def sample_member():
    """Fixture providing a sample member for testing."""
    return Member(
        id="member-001",
        name="Test User",
        email="test@example.com",
        status="active",
        access_level=AccessLevel.NONE,
    )


class TestMemberLifecycle:
    """Tests for the full member lifecycle: create, update, delete."""

    def test_full_member_lifecycle(self, member_service, sample_member):
        """Test creating a member, updating it, and then deleting it."""
        # Create member
        member_service.repository.create.return_value = sample_member
        created = member_service.create_member(
            name="Test User",
            email="test@example.com",
        )
        assert created is not None
        assert created.id == "member-001"
        assert created.name == "Test User"
        assert created.email == "test@example.com"
        member_service.repository.create.assert_called_once()

        # Update member
        updated_member = Member(
            id="member-001",
            name="Updated User",
            email="updated@example.com",
            status="active",
            access_level=AccessLevel.NONE,
        )
        member_service.repository.update.return_value = updated_member
        updated = member_service.update_member(
            member_id="member-001",
            name="Updated User",
            email="updated@example.com",
        )
        assert updated is not None
        assert updated.name == "Updated User"
        assert updated.email == "updated@example.com"
        member_service.repository.update.assert_called_once_with(
            "member-001",
            name="Updated User",
            email="updated@example.com",
        )

        # Delete member
        member_service.repository.delete.return_value = True
        result = member_service.delete_member(member_id="member-001")
        assert result is True
        member_service.repository.delete.assert_called_once_with("member-001")


class TestMemberVerificationFlow:
    """Tests for member verification workflow."""

    def test_member_verification_flow(self, member_service, sample_member):
        """Test creating a member, verifying them, and checking their status."""
        # Create member (unverified)
        unverified_member = Member(
            id="member-002",
            name="Unverified User",
            email="unverified@example.com",
            status="pending",
            access_level=AccessLevel.NONE,
        )
        member_service.repository.create.return_value = unverified_member
        created = member_service.create_member(
            name="Unverified User",
            email="unverified@example.com",
        )
        assert created is not None
        assert created.status == "pending"

        # Verify member
        verified_member = Member(
            id="member-002",
            name="Unverified User",
            email="unverified@example.com",
            status="verified",
            access_level=AccessLevel.BASIC,
        )
        member_service.repository.verify.return_value = verified_member
        verified = member_service.verify_member(member_id="member-002")
        assert verified is not None
        assert verified.status == "verified"
        member_service.repository.verify.assert_called_once_with("member-002")

        # Get member status
        member_service.repository.get.return_value = verified_member
        status = member_service.get_member_status(member_id="member-002")
        assert status == "verified"
        member_service.repository.get.assert_called_with("member-002")


class TestMemberAccessFlow:
    """Tests for member access grant and revoke workflow."""

    def test_member_access_flow(self, member_service, sample_member):
        """Test creating a member, granting access, and revoking access."""
        # Create member
        member_service.repository.create.return_value = sample_member
        created = member_service.create_member(
            name="Test User",
            email="test@example.com",
        )
        assert created is not None
        assert created.access_level == AccessLevel.NONE

        # Grant access
        granted_member = Member(
            id="member-001",
            name="Test User",
            email="test@example.com",
            status="active",
            access_level=AccessLevel.PREMIUM,
        )
        member_service.repository.grant_access.return_value = granted_member
        granted = member_service.grant_access(
            member_id="member-001",
            access_level=AccessLevel.PREMIUM,
        )
        assert granted is not None
        assert granted.access_level == AccessLevel.PREMIUM
        member_service.repository.grant_access.assert_called_once_with(
            "member-001",
            AccessLevel.PREMIUM,
        )

        # Revoke access
        revoked_member = Member(
            id="member-001",
            name="Test User",
            email="test@example.com",
            status="active",
            access_level=AccessLevel.NONE,
        )
        member_service.repository.revoke_access.return_value = revoked_member
        revoked = member_service.revoke_access(member_id="member-001")
        assert revoked is not None
        assert revoked.access_level == AccessLevel.NONE
        member_service.repository.revoke_access.assert_called_once_with("member-001")
