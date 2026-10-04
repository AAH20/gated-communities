"""Comprehensive service tests for the InvitationService."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gated_communities.models.invitation import (
    Invitation,
    InvitationCreate,
    InvitationStatus,
    InvitationUpdate,
)
from gated_communities.services.invitation_service import InvitationService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_uow():
    """Return a mock Unit of Work with async repository methods."""
    uow = MagicMock()
    uow.invitations = AsyncMock()
    uow.communities = AsyncMock()
    uow.users = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow


@pytest.fixture
def sample_invitation():
    """Return a sample Invitation model instance."""
    now = datetime.now(timezone.utc)
    return Invitation(
        id="inv-001",
        community_id="comm-001",
        inviter_id="user-001",
        invitee_email="invitee@example.com",
        invitee_id=None,
        role="member",
        status=InvitationStatus.PENDING,
        token="tok-abc-123",
        expires_at=now + timedelta(days=7),
        created_at=now,
        updated_at=now,
        accepted_at=None,
        revoked_at=None,
        revoked_by=None,
        max_uses=1,
        use_count=0,
        metadata={},
    )


@pytest.fixture
def sample_invitation_create():
    """Return a sample InvitationCreate schema."""
    return InvitationCreate(
        community_id="comm-001",
        inviter_id="user-001",
        invitee_email="new_invitee@example.com",
        role="member",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        max_uses=1,
        metadata={},
    )


@pytest.fixture
def sample_invitation_update():
    """Return a sample InvitationUpdate schema."""
    return InvitationUpdate(
        role="admin",
        status=InvitationStatus.ACCEPTED,
        max_uses=5,
    )


@pytest.fixture
def invitation_service(mock_uow):
    """Return an InvitationService backed by the mock UoW."""
    return InvitationService(uow=mock_uow)


# ---------------------------------------------------------------------------
# 1. test_get_invitation
# ---------------------------------------------------------------------------


class TestGetInvitation:
    """Tests for InvitationService.get_invitation."""

    @pytest.mark.asyncio
    async def test_get_invitation_returns_invitation(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """get_invitation returns the invitation when found."""
        mock_uow.invitations.get_by_id.return_value = sample_invitation

        result = await invitation_service.get_invitation("inv-001")

        assert result is not None
        assert result.id == "inv-001"
        assert result.community_id == "comm-001"
        assert result.invitee_email == "invitee@example.com"
        assert result.status == InvitationStatus.PENDING
        mock_uow.invitations.get_by_id.assert_awaited_once_with("inv-001")

    @pytest.mark.asyncio
    async def test_get_invitation_returns_none_when_not_found(
        self, invitation_service, mock_uow
    ):
        """get_invitation returns None when the invitation does not exist."""
        mock_uow.invitations.get_by_id.return_value = None

        result = await invitation_service.get_invitation("nonexistent")

        assert result is None
        mock_uow.invitations.get_by_id.assert_awaited_once_with("nonexistent")

    @pytest.mark.asyncio
    async def test_get_invitation_by_token(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """get_invitation_by_token returns the invitation for a valid token."""
        mock_uow.invitations.get_by_token.return_value = sample_invitation

        result = await invitation_service.get_invitation_by_token("tok-abc-123")

        assert result is not None
        assert result.token == "tok-abc-123"
        mock_uow.invitations.get_by_token.assert_awaited_once_with("tok-abc-123")

    @pytest.mark.asyncio
    async def test_get_invitation_by_token_returns_none_for_invalid_token(
        self, invitation_service, mock_uow
    ):
        """get_invitation_by_token returns None for an unknown token."""
        mock_uow.invitations.get_by_token.return_value = None

        result = await invitation_service.get_invitation_by_token("bad-token")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_invitation_propagates_repository_exception(
        self, invitation_service, mock_uow
    ):
        """get_invitation propagates exceptions from the repository."""
        mock_uow.invitations.get_by_id.side_effect = ConnectionError("DB down")

        with pytest.raises(ConnectionError, match="DB down"):
            await invitation_service.get_invitation("inv-001")


# ---------------------------------------------------------------------------
# 2. test_list_invitations
# ---------------------------------------------------------------------------


class TestListInvitations:
    """Tests for InvitationService.list_invitations with filters."""

    @pytest.mark.asyncio
    async def test_list_invitations_returns_all_when_no_filters(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """list_invitations returns all invitations when no filters are given."""
        mock_uow.invitations.list.return_value = [sample_invitation]

        result = await invitation_service.list_invitations()

        assert len(result) == 1
        assert result[0].id == "inv-001"
        mock_uow.invitations.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_invitations_filter_by_community(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """list_invitations filters by community_id."""
        mock_uow.invitations.list.return_value = [sample_invitation]

        result = await invitation_service.list_invitations(
            community_id="comm-001"
        )

        assert len(result) == 1
        assert result[0].community_id == "comm-001"
        mock_uow.invitations.list.assert_awaited_once()
        call_kwargs = mock_uow.invitations.list.call_args.kwargs
        assert call_kwargs.get("community_id") == "comm-001"

    @pytest.mark.asyncio
    async def test_list_invitations_filter_by_status(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """list_invitations filters by status."""
        mock_uow.invitations.list.return_value = [sample_invitation]

        result = await invitation_service.list_invitations(
            status=InvitationStatus.PENDING
        )

        assert len(result) == 1
        call_kwargs = mock_uow.invitations.list.call_args.kwargs
        assert call_kwargs.get("status") == InvitationStatus.PENDING

    @pytest.mark.asyncio
    async def test_list_invitations_filter_by_inviter(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """list_invitations filters by inviter_id."""
        mock_uow.invitations.list.return_value = [sample_invitation]

        result = await invitation_service.list_invitations(inviter_id="user-001")

        assert len(result) == 1
        call_kwargs = mock_uow.invitations.list.call_args.kwargs
        assert call_kwargs.get("inviter_id") == "user-001"

    @pytest.mark.asyncio
    async def test_list_invitations_filter_by_email(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """list_invitations filters by invitee_email."""
        mock_uow.invitations.list.return_value = [sample_invitation]

        result = await invitation_service.list_invitations(
            invitee_email="invitee@example.com"
        )

        assert len(result) == 1
        call_kwargs = mock_uow.invitations.list.call_args.kwargs
        assert call_kwargs.get("invitee_email") == "invitee@example.com"

    @pytest.mark.asyncio
    async def test_list_invitations_combined_filters(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """list_invitations applies multiple filters simultaneously."""
        mock_uow.invitations.list.return_value = [sample_invitation]

        result = await invitation_service.list_invitations(
            community_id="comm-001",
            status=InvitationStatus.PENDING,
            inviter_id="user-001",
        )

        assert len(result) == 1
        call_kwargs = mock_uow.invitations.list.call_args.kwargs
        assert call_kwargs.get("community_id") == "comm-001"
        assert call_kwargs.get("status") == InvitationStatus.PENDING
        assert call_kwargs.get("inviter_id") == "user-001"

    @pytest.mark.asyncio
    async def test_list_invitations_returns_empty_list(
        self, invitation_service, mock_uow
    ):
        """list_invitations returns an empty list when nothing matches."""
        mock_uow.invitations.list.return_value = []

        result = await invitation_service.list_invitations(
            community_id="comm-no-match"
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_list_invitations_with_pagination(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """list_invitations passes pagination parameters through."""
        mock_uow.invitations.list.return_value = [sample_invitation]

        result = await invitation_service.list_invitations(skip=10, limit=5)

        assert len(result) == 1
        call_kwargs = mock_uow.invitations.list.call_args.kwargs
        assert call_kwargs.get("skip") == 10
        assert call_kwargs.get("limit") == 5

    @pytest.mark.asyncio
    async def test_list_invitations_default_pagination(
        self, invitation_service, mock_uow
    ):
        """list_invitations uses default pagination values."""
        mock_uow.invitations.list.return_value = []

        await invitation_service.list_invitations()

        call_kwargs = mock_uow.invitations.list.call_args.kwargs
        assert call_kwargs.get("skip", 0) == 0
        assert call_kwargs.get("limit", 100) == 100


# ---------------------------------------------------------------------------
# 3. test_create_invitation
# ---------------------------------------------------------------------------


class TestCreateInvitation:
    """Tests for InvitationService.create_invitation."""

    @pytest.mark.asyncio
    async def test_create_invitation_success(
        self, invitation_service, mock_uow, sample_invitation_create, sample_invitation
    ):
        """create_invitation creates and returns a new invitation."""
        mock_uow.communities.get_by_id.return_value = MagicMock(id="comm-001")
        mock_uow.users.get_by_id.return_value = MagicMock(id="user-001")
        mock_uow.invitations.create.return_value = sample_invitation

        result = await invitation_service.create_invitation(sample_invitation_create)

        assert result is not None
        assert result.id == "inv-001"
        assert result.community_id == "comm-001"
        assert result.invitee_email == "invitee@example.com"
        assert result.status == InvitationStatus.PENDING
        mock_uow.invitations.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_invitation_generates_token(
        self, invitation_service, mock_uow, sample_invitation_create
    ):
        """create_invitation generates a unique token for the invitation."""
        mock_uow.communities.get_by_id.return_value = MagicMock(id="comm-001")
        mock_uow.users.get_by_id.return_value = MagicMock(id="user-001")

        created_invitation = Invitation(
            id="inv-new",
            community_id="comm-001",
            inviter_id="user-001",
            invitee_email="new_invitee@example.com",
            role="member",
            status=InvitationStatus.PENDING,
            token="generated-token-xyz",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_uow.invitations.create.return_value = created_invitation

        result = await invitation_service.create_invitation(sample_invitation_create)

        assert result.token is not None
        assert len(result.token) > 0

    @pytest.mark.asyncio
    async def test_create_invitation_sets_default_status_pending(
        self, invitation_service, mock_uow, sample_invitation_create
    ):
        """create_invitation sets status to PENDING by default."""
        mock_uow.communities.get_by_id.return_value = MagicMock(id="comm-001")
        mock_uow.users.get_by_id.return_value = MagicMock(id="user-001")

        created_invitation = Invitation(
            id="inv-new",
            community_id="comm-001",
            inviter_id="user-001",
            invitee_email="new_invitee@example.com",
            role="member",
            status=InvitationStatus.PENDING,
            token="tok-new",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_uow.invitations.create.return_value = created_invitation

        result = await invitation_service.create_invitation(sample_invitation_create)

        assert result.status == InvitationStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_invitation_raises_for_nonexistent_community(
        self, invitation_service, mock_uow, sample_invitation_create
    ):
        """create_invitation raises ValueError when community does not exist."""
        mock_uow.communities.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Community not found"):
            await invitation_service.create_invitation(sample_invitation_create)

    @pytest.mark.asyncio
    async def test_create_invitation_raises_for_nonexistent_inviter(
        self, invitation_service, mock_uow, sample_invitation_create
    ):
        """create_invitation raises ValueError when inviter does not exist."""
        mock_uow.communities.get_by_id.return_value = MagicMock(id="comm-001")
        mock_uow.users.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Inviter not found"):
            await invitation_service.create_invitation(sample_invitation_create)

    @pytest.mark.asyncio
    async def test_create_invitation_commits_uow(
        self, invitation_service, mock_uow, sample_invitation_create, sample_invitation
    ):
        """create_invitation commits the unit of work on success."""
        mock_uow.communities.get_by_id.return_value = MagicMock(id="comm-001")
        mock_uow.users.get_by_id.return_value = MagicMock(id="user-001")
        mock_uow.invitations.create.return_value = sample_invitation

        await invitation_service.create_invitation(sample_invitation_create)

        mock_uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_invitation_does_not_commit_on_failure(
        self, invitation_service, mock_uow, sample_invitation_create
    ):
        """create_invitation does not commit when validation fails."""
        mock_uow.communities.get_by_id.return_value = None

        with pytest.raises(ValueError):
            await invitation_service.create_invitation(sample_invitation_create)

        mock_uow.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_invitation_with_custom_role(
        self, invitation_service, mock_uow
    ):
        """create_invitation respects a custom role."""
        create_data = InvitationCreate(
            community_id="comm-001",
            inviter_id="user-001",
            invitee_email="admin@example.com",
            role="admin",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        mock_uow.communities.get_by_id.return_value = MagicMock(id="comm-001")
        mock_uow.users.get_by_id.return_value = MagicMock(id="user-001")

        created_invitation = Invitation(
            id="inv-admin",
            community_id="comm-001",
            inviter_id="user-001",
            invitee_email="admin@example.com",
            role="admin",
            status=InvitationStatus.PENDING,
            token="tok-admin",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_uow.invitations.create.return_value = created_invitation

        result = await invitation_service.create_invitation(create_data)

        assert result.role == "admin"

    @pytest.mark.asyncio
    async def test_create_invitation_with_max_uses(
        self, invitation_service, mock_uow
    ):
        """create_invitation respects max_uses setting."""
        create_data = InvitationCreate(
            community_id="comm-001",
            inviter_id="user-001",
            invitee_email="multi@example.com",
            role="member",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            max_uses=10,
        )
        mock_uow.communities.get_by_id.return_value = MagicMock(id="comm-001")
        mock_uow.users.get_by_id.return_value = MagicMock(id="user-001")

        created_invitation = Invitation(
            id="inv-multi",
            community_id="comm-001",
            inviter_id="user-001",
            invitee_email="multi@example.com",
            role="member",
            status=InvitationStatus.PENDING,
            token="tok-multi",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            max_uses=10,
            use_count=0,
        )
        mock_uow.invitations.create.return_value = created_invitation

        result = await invitation_service.create_invitation(create_data)

        assert result.max_uses == 10
        assert result.use_count == 0


# ---------------------------------------------------------------------------
# 4. test_update_invitation
# ---------------------------------------------------------------------------


class TestUpdateInvitation:
    """Tests for InvitationService.update_invitation."""

    @pytest.mark.asyncio
    async def test_update_invitation_success(
        self, invitation_service, mock_uow, sample_invitation, sample_invitation_update
    ):
        """update_invitation updates and returns the invitation."""
        mock_uow.invitations.get_by_id.return_value = sample_invitation

        updated_invitation = Invitation(
            id="inv-001",
            community_id="comm-001",
            inviter_id="user-001",
            invitee_email="invitee@example.com",
            role="admin",
            status=InvitationStatus.ACCEPTED,
            token="tok-abc-123",
            expires_at=sample_invitation.expires_at,
            created_at=sample_invitation.created_at,
            updated_at=datetime.now(timezone.utc),
            max_uses=5,
            use_count=0,
        )
        mock_uow.invitations.update.return_value = updated_invitation

        result = await invitation_service.update_invitation(
            "inv-001", sample_invitation_update
        )

        assert result is not None
        assert result.role == "admin"
        assert result.status == InvitationStatus.ACCEPTED
        assert result.max_uses == 5
        mock_uow.invitations.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_invitation_returns_none_when_not_found(
        self, invitation_service, mock_uow, sample_invitation_update
    ):
        """update_invitation returns None when the invitation does not exist."""
        mock_uow.invitations.get_by_id.return_value = None

        result = await invitation_service.update_invitation(
            "nonexistent", sample_invitation_update
        )

        assert result is None
        mock_uow.invitations.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_invitation_partial_update(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """update_invitation applies only the provided fields."""
        mock_uow.invitations.get_by_id.return_value = sample_invitation

        partial_update = InvitationUpdate(role="moderator")
        updated_invitation = Invitation(
            id="inv-001",
            community_id="comm-001",
            inviter_id="user-001",
            invitee_email="invitee@example.com",
            role="moderator",
            status=InvitationStatus.PENDING,
            token="tok-abc-123",
            expires_at=sample_invitation.expires_at,
            created_at=sample_invitation.created_at,
            updated_at=datetime.now(timezone.utc),
        )
        mock_uow.invitations.update.return_value = updated_invitation

        result = await invitation_service.update_invitation(
            "inv-001", partial_update
        )

        assert result.role == "moderator"
        assert result.status == InvitationStatus.PENDING

    @pytest.mark.asyncio
    async def test_update_invitation_status_to_revoked(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """update_invitation can set status to REVOKED."""
        mock_uow.invitations.get_by_id.return_value = sample_invitation

        revoke_update = InvitationUpdate(status=InvitationStatus.REVOKED)
        updated_invitation = Invitation(
            id="inv-001",
            community_id="comm-001",
            inviter_id="user-001",
            invitee_email="invitee@example.com",
            role="member",
            status=InvitationStatus.REVOKED,
            token="tok-abc-123",
            expires_at=sample_invitation.expires_at,
            created_at=sample_invitation.created_at,
            updated_at=datetime.now(timezone.utc),
            revoked_at=datetime.now(timezone.utc),
        )
        mock_uow.invitations.update.return_value = updated_invitation

        result = await invitation_service.update_invitation("inv-001", revoke_update)

        assert result.status == InvitationStatus.REVOKED
        assert result.revoked_at is not None

    @pytest.mark.asyncio
    async def test_update_invitation_commits_uow(
        self, invitation_service, mock_uow, sample_invitation, sample_invitation_update
    ):
        """update_invitation commits the unit of work on success."""
        mock_uow.invitations.get_by_id.return_value = sample_invitation
        mock_uow.invitations.update.return_value = sample_invitation

        await invitation_service.update_invitation("inv-001", sample_invitation_update)

        mock_uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_invitation_does_not_commit_when_not_found(
        self, invitation_service, mock_uow, sample_invitation_update
    ):
        """update_invitation does not commit when the invitation is not found."""
        mock_uow.invitations.get_by_id.return_value = None

        await invitation_service.update_invitation(
            "nonexistent", sample_invitation_update
        )

        mock_uow.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_invitation_increments_use_count(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """update_invitation can increment the use count."""
        mock_uow.invitations.get_by_id.return_value = sample_invitation

        use_update = InvitationUpdate()
        updated_invitation = Invitation(
            id="inv-001",
            community_id="comm-001",
            inviter_id="user-001",
            invitee_email="invitee@example.com",
            role="member",
            status=InvitationStatus.PENDING,
            token="tok-abc-123",
            expires_at=sample_invitation.expires_at,
            created_at=sample_invitation.created_at,
            updated_at=datetime.now(timezone.utc),
            use_count=1,
        )
        mock_uow.invitations.update.return_value = updated_invitation

        result = await invitation_service.update_invitation("inv-001", use_update)

        assert result.use_count == 1


# ---------------------------------------------------------------------------
# 5. test_delete_invitation
# ---------------------------------------------------------------------------


class TestDeleteInvitation:
    """Tests for InvitationService.delete_invitation."""

    @pytest.mark.asyncio
    async def test_delete_invitation_success(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """delete_invitation deletes and returns True on success."""
        mock_uow.invitations.get_by_id.return_value = sample_invitation
        mock_uow.invitations.delete.return_value = True

        result = await invitation_service.delete_invitation("inv-001")

        assert result is True
        mock_uow.invitations.delete.assert_awaited_once_with("inv-001")

    @pytest.mark.asyncio
    async def test_delete_invitation_returns_false_when_not_found(
        self, invitation_service, mock_uow
    ):
        """delete_invitation returns False when the invitation does not exist."""
        mock_uow.invitations.get_by_id.return_value = None

        result = await invitation_service.delete_invitation("nonexistent")

        assert result is False
        mock_uow.invitations.delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_invitation_commits_uow(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """delete_invitation commits the unit of work on success."""
        mock_uow.invitations.get_by_id.return_value = sample_invitation
        mock_uow.invitations.delete.return_value = True

        await invitation_service.delete_invitation("inv-001")

        mock_uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_invitation_does_not_commit_when_not_found(
        self, invitation_service, mock_uow
    ):
        """delete_invitation does not commit when the invitation is not found."""
        mock_uow.invitations.get_by_id.return_value = None

        await invitation_service.delete_invitation("nonexistent")

        mock_uow.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_invitation_propagates_repository_exception(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """delete_invitation propagates exceptions from the repository."""
        mock_uow.invitations.get_by_id.return_value = sample_invitation
        mock_uow.invitations.delete.side_effect = ConnectionError("DB error")

        with pytest.raises(ConnectionError, match="DB error"):
            await invitation_service.delete_invitation("inv-001")

    @pytest.mark.asyncio
    async def test_delete_invitation_revokes_token(
        self, invitation_service, mock_uow, sample_invitation
    ):
        """delete_invitation effectively revokes the invitation token."""
        mock_uow.invitations.get_by_id.return_value = sample_invitation
        mock_uow.invitations.delete.return_value = True

        result = await invitation_service.delete_invitation("inv-001")

        assert result is True
        mock_uow.invitations.delete.assert_awaited_once_with("inv-001")
