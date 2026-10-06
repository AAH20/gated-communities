"""Comprehensive service tests for the access control service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from gated_communities.services.access_service import (
    AccessService,
    check_access,
    get_access_permissions,
    grant_access,
    revoke_access,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Provide a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_redis():
    """Provide a mock Redis client."""
    return MagicMock()


@pytest.fixture
def access_service(mock_db, mock_redis):
    """Provide an AccessService instance with mocked dependencies."""
    return AccessService(db=mock_db, redis=mock_redis)


@pytest.fixture
def sample_user_id():
    return "user-123"


@pytest.fixture
def sample_community_id():
    return "community-456"


@pytest.fixture
def sample_permission():
    return "read"


@pytest.fixture
def sample_permissions():
    return ["read", "write", "moderate"]


@pytest.fixture
def sample_grant_record():
    return {
        "id": "grant-789",
        "user_id": "user-123",
        "community_id": "community-456",
        "permissions": ["read", "write"],
        "granted_by": "admin-001",
        "granted_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "expires_at": datetime(2026, 12, 31, tzinfo=timezone.utc),
        "is_active": True,
    }


@pytest.fixture
def sample_expired_grant_record():
    return {
        "id": "grant-expired",
        "user_id": "user-123",
        "community_id": "community-456",
        "permissions": ["read"],
        "granted_by": "admin-001",
        "granted_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "expires_at": datetime(2025, 6, 1, tzinfo=timezone.utc),
        "is_active": True,
    }


@pytest.fixture
def sample_revoked_grant_record():
    return {
        "id": "grant-revoked",
        "user_id": "user-123",
        "community_id": "community-456",
        "permissions": ["read"],
        "granted_by": "admin-001",
        "granted_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "expires_at": datetime(2026, 12, 31, tzinfo=timezone.utc),
        "is_active": False,
    }


# ---------------------------------------------------------------------------
# Tests for check_access
# ---------------------------------------------------------------------------


class TestCheckAccess:
    """Tests for the check_access function."""

    def test_check_access_returns_true_when_user_has_permission(
        self, access_service, sample_user_id, sample_community_id, sample_permission
    ):
        """User with an active grant containing the permission is allowed."""
        access_service.has_permission = MagicMock(return_value=True)

        result = check_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permission=sample_permission,
            service=access_service,
        )

        assert result is True
        access_service.has_permission.assert_called_once_with(
            sample_user_id, sample_community_id, sample_permission
        )

    def test_check_access_returns_false_when_user_lacks_permission(
        self, access_service, sample_user_id, sample_community_id, sample_permission
    ):
        """User without the required permission is denied."""
        access_service.has_permission = MagicMock(return_value=False)

        result = check_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permission=sample_permission,
            service=access_service,
        )

        assert result is False

    def test_check_access_with_multiple_permissions(
        self, access_service, sample_user_id, sample_community_id, sample_permissions
    ):
        """User with multiple permissions is allowed when any matches."""
        access_service.has_permission = MagicMock(side_effect=[False, True, False])

        result = check_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permission="write",
            service=access_service,
        )

        assert result is True

    def test_check_access_denies_when_no_grant_exists(
        self, access_service, sample_user_id, sample_community_id
    ):
        """User with no grant record is denied access."""
        access_service.has_permission = MagicMock(return_value=False)

        result = check_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permission="read",
            service=access_service,
        )

        assert result is False

    def test_check_access_denies_when_grant_is_expired(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Expired grants do not confer access."""
        access_service.has_permission = MagicMock(return_value=False)

        result = check_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permission="read",
            service=access_service,
        )

        assert result is False

    def test_check_access_denies_when_grant_is_revoked(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Revoked grants do not confer access."""
        access_service.has_permission = MagicMock(return_value=False)

        result = check_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permission="read",
            service=access_service,
        )

        assert result is False

    def test_check_access_with_empty_permission_string(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Empty permission string is handled gracefully."""
        access_service.has_permission = MagicMock(return_value=False)

        result = check_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permission="",
            service=access_service,
        )

        assert result is False

    def test_check_access_with_none_permission(
        self, access_service, sample_user_id, sample_community_id
    ):
        """None permission is handled gracefully."""
        access_service.has_permission = MagicMock(return_value=False)

        result = check_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permission=None,
            service=access_service,
        )

        assert result is False

    def test_check_access_caches_result(
        self, access_service, sample_user_id, sample_community_id, sample_permission
    ):
        """Repeated checks use cached results when available."""
        access_service.has_permission = MagicMock(return_value=True)

        result1 = check_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permission=sample_permission,
            service=access_service,
        )
        result2 = check_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permission=sample_permission,
            service=access_service,
        )

        assert result1 is True
        assert result2 is True

    def test_check_access_different_communities_are_isolated(
        self, access_service, sample_user_id, sample_permission
    ):
        """Access in one community does not grant access in another."""
        access_service.has_permission = MagicMock(side_effect=[True, False])

        result1 = check_access(
            user_id=sample_user_id,
            community_id="community-A",
            permission=sample_permission,
            service=access_service,
        )
        result2 = check_access(
            user_id=sample_user_id,
            community_id="community-B",
            permission=sample_permission,
            service=access_service,
        )

        assert result1 is True
        assert result2 is False


# ---------------------------------------------------------------------------
# Tests for grant_access
# ---------------------------------------------------------------------------


class TestGrantAccess:
    """Tests for the grant_access function."""

    def test_grant_access_creates_new_grant(
        self, access_service, sample_user_id, sample_community_id, sample_permission
    ):
        """Granting access creates a new grant record."""
        access_service.create_grant = MagicMock(return_value={"id": "new-grant-001"})

        result = grant_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permissions=[sample_permission],
            granted_by="admin-001",
            service=access_service,
        )

        assert result["id"] == "new-grant-001"
        access_service.create_grant.assert_called_once()

    def test_grant_access_with_multiple_permissions(
        self, access_service, sample_user_id, sample_community_id, sample_permissions
    ):
        """Granting multiple permissions at once."""
        access_service.create_grant = MagicMock(return_value={"id": "new-grant-002"})

        result = grant_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permissions=sample_permissions,
            granted_by="admin-001",
            service=access_service,
        )

        assert result["id"] == "new-grant-002"
        call_kwargs = access_service.create_grant.call_args
        assert call_kwargs.kwargs["permissions"] == sample_permissions

    def test_grant_access_with_expiration(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Grant with an expiration date."""
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        access_service.create_grant = MagicMock(return_value={"id": "new-grant-003"})

        result = grant_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permissions=["read"],
            granted_by="admin-001",
            expires_at=expires,
            service=access_service,
        )

        assert result["id"] == "new-grant-003"
        call_kwargs = access_service.create_grant.call_args
        assert call_kwargs.kwargs["expires_at"] == expires

    def test_grant_access_without_expiration(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Grant without expiration creates a permanent grant."""
        access_service.create_grant = MagicMock(return_value={"id": "new-grant-004"})

        result = grant_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permissions=["read"],
            granted_by="admin-001",
            service=access_service,
        )

        assert result["id"] == "new-grant-004"
        call_kwargs = access_service.create_grant.call_args
        assert call_kwargs.kwargs.get("expires_at") is None

    def test_grant_access_updates_existing_grant(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Granting access to a user who already has a grant updates it."""
        access_service.get_active_grant = MagicMock(
            return_value={"id": "existing-grant", "permissions": ["read"]}
        )
        access_service.update_grant = MagicMock(
            return_value={"id": "existing-grant", "permissions": ["read", "write"]}
        )

        result = grant_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permissions=["read", "write"],
            granted_by="admin-001",
            service=access_service,
        )

        assert result["permissions"] == ["read", "write"]
        access_service.update_grant.assert_called_once()

    def test_grant_access_clears_cache(
        self, access_service, sample_user_id, sample_community_id, mock_redis
    ):
        """Granting access invalidates cached permissions."""
        access_service.create_grant = MagicMock(return_value={"id": "new-grant-005"})

        grant_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permissions=["read"],
            granted_by="admin-001",
            service=access_service,
        )

        mock_redis.delete.assert_called()

    def test_grant_access_with_empty_permissions_list(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Granting with empty permissions list is handled."""
        access_service.create_grant = MagicMock(return_value={"id": "new-grant-006"})

        result = grant_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permissions=[],
            granted_by="admin-001",
            service=access_service,
        )

        assert result["id"] == "new-grant-006"

    def test_grant_access_raises_on_database_error(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Database errors during grant creation propagate."""
        access_service.create_grant = MagicMock(
            side_effect=Exception("Database connection failed")
        )

        with pytest.raises(Exception, match="Database connection failed"):
            grant_access(
                user_id=sample_user_id,
                community_id=sample_community_id,
                permissions=["read"],
                granted_by="admin-001",
                service=access_service,
            )

    def test_grant_access_with_duplicate_permission(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Duplicate permissions in the list are deduplicated."""
        access_service.create_grant = MagicMock(return_value={"id": "new-grant-007"})

        result = grant_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permissions=["read", "read", "write", "write"],
            granted_by="admin-001",
            service=access_service,
        )

        assert result["id"] == "new-grant-007"
        call_kwargs = access_service.create_grant.call_args
        perms = call_kwargs.kwargs["permissions"]
        assert len(perms) == len(set(perms))


# ---------------------------------------------------------------------------
# Tests for revoke_access
# ---------------------------------------------------------------------------


class TestRevokeAccess:
    """Tests for the revoke_access function."""

    def test_revoke_access_deactivates_grant(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Revoking access deactivates the grant record."""
        access_service.deactivate_grant = MagicMock(return_value={"id": "grant-789", "is_active": False})

        result = revoke_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            revoked_by="admin-001",
            service=access_service,
        )

        assert result["is_active"] is False
        access_service.deactivate_grant.assert_called_once()

    def test_revoke_access_clears_cache(
        self, access_service, sample_user_id, sample_community_id, mock_redis
    ):
        """Revoking access invalidates cached permissions."""
        access_service.deactivate_grant = MagicMock(return_value={"id": "grant-789", "is_active": False})

        revoke_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            revoked_by="admin-001",
            service=access_service,
        )

        mock_redis.delete.assert_called()

    def test_revoke_access_nonexistent_grant(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Revoking access for a user with no grant is a no-op."""
        access_service.deactivate_grant = MagicMock(return_value=None)

        result = revoke_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            revoked_by="admin-001",
            service=access_service,
        )

        assert result is None

    def test_revoke_access_already_revoked(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Revoking an already revoked grant is idempotent."""
        access_service.deactivate_grant = MagicMock(
            return_value={"id": "grant-789", "is_active": False}
        )

        result = revoke_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            revoked_by="admin-001",
            service=access_service,
        )

        assert result["is_active"] is False

    def test_revoke_access_with_specific_permission(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Revoking a specific permission from a user's grant."""
        access_service.remove_permission = MagicMock(
            return_value={"id": "grant-789", "permissions": ["read"]}
        )

        result = revoke_access(
            user_id=sample_user_id,
            community_id=sample_community_id,
            permission="write",
            revoked_by="admin-001",
            service=access_service,
        )

        assert "write" not in result["permissions"]
        access_service.remove_permission.assert_called_once()

    def test_revoke_access_raises_on_database_error(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Database errors during revocation propagate."""
        access_service.deactivate_grant = MagicMock(
            side_effect=Exception("Database connection failed")
        )

        with pytest.raises(Exception, match="Database connection failed"):
            revoke_access(
                user_id=sample_user_id,
                community_id=sample_community_id,
                revoked_by="admin-001",
                service=access_service,
            )

    def test_revoke_access_does_not_affect_other_communities(
        self, access_service, sample_user_id
    ):
        """Revoking access in one community does not affect others."""
        access_service.deactivate_grant = MagicMock(return_value={"id": "grant-789", "is_active": False})

        revoke_access(
            user_id=sample_user_id,
            community_id="community-A",
            revoked_by="admin-001",
            service=access_service,
        )

        call_kwargs = access_service.deactivate_grant.call_args
        assert call_kwargs.kwargs["community_id"] == "community-A"


# ---------------------------------------------------------------------------
# Tests for get_access_permissions
# ---------------------------------------------------------------------------


class TestGetAccessPermissions:
    """Tests for the get_access_permissions function."""

    def test_get_access_permissions_returns_active_permissions(
        self, access_service, sample_user_id, sample_community_id, sample_permissions
    ):
        """Returns the list of active permissions for a user."""
        access_service.get_permissions = MagicMock(return_value=sample_permissions)

        result = get_access_permissions(
            user_id=sample_user_id,
            community_id=sample_community_id,
            service=access_service,
        )

        assert result == sample_permissions
        access_service.get_permissions.assert_called_once_with(
            sample_user_id, sample_community_id
        )

    def test_get_access_permissions_empty_when_no_grant(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Returns empty list when user has no grant."""
        access_service.get_permissions = MagicMock(return_value=[])

        result = get_access_permissions(
            user_id=sample_user_id,
            community_id=sample_community_id,
            service=access_service,
        )

        assert result == []

    def test_get_access_permissions_empty_when_grant_expired(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Returns empty list when the grant has expired."""
        access_service.get_permissions = MagicMock(return_value=[])

        result = get_access_permissions(
            user_id=sample_user_id,
            community_id=sample_community_id,
            service=access_service,
        )

        assert result == []

    def test_get_access_permissions_empty_when_grant_revoked(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Returns empty list when the grant has been revoked."""
        access_service.get_permissions = MagicMock(return_value=[])

        result = get_access_permissions(
            user_id=sample_user_id,
            community_id=sample_community_id,
            service=access_service,
        )

        assert result == []

    def test_get_access_permissions_caches_result(
        self, access_service, sample_user_id, sample_community_id, sample_permissions, mock_redis
    ):
        """Permissions are cached in Redis for subsequent calls."""
        access_service.get_permissions = MagicMock(return_value=sample_permissions)
        mock_redis.get.return_value = None

        result1 = get_access_permissions(
            user_id=sample_user_id,
            community_id=sample_community_id,
            service=access_service,
        )
        result2 = get_access_permissions(
            user_id=sample_user_id,
            community_id=sample_community_id,
            service=access_service,
        )

        assert result1 == sample_permissions
        assert result2 == sample_permissions

    def test_get_access_permissions_different_communities(
        self, access_service, sample_user_id
    ):
        """Permissions are isolated per community."""
        access_service.get_permissions = MagicMock(side_effect=[["read"], ["write", "moderate"]])

        result_a = get_access_permissions(
            user_id=sample_user_id,
            community_id="community-A",
            service=access_service,
        )
        result_b = get_access_permissions(
            user_id=sample_user_id,
            community_id="community-B",
            service=access_service,
        )

        assert result_a == ["read"]
        assert result_b == ["write", "moderate"]

    def test_get_access_permissions_with_single_permission(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Returns a single-element list for one permission."""
        access_service.get_permissions = MagicMock(return_value=["read"])

        result = get_access_permissions(
            user_id=sample_user_id,
            community_id=sample_community_id,
            service=access_service,
        )

        assert result == ["read"]

    def test_get_access_permissions_returns_copy(
        self, access_service, sample_user_id, sample_community_id, sample_permissions
    ):
        """Mutating the returned list does not affect internal state."""
        access_service.get_permissions = MagicMock(return_value=list(sample_permissions))

        result = get_access_permissions(
            user_id=sample_user_id,
            community_id=sample_community_id,
            service=access_service,
        )
        result.append("admin")

        assert "admin" not in sample_permissions

    def test_get_access_permissions_raises_on_database_error(
        self, access_service, sample_user_id, sample_community_id
    ):
        """Database errors during permission retrieval propagate."""
        access_service.get_permissions = MagicMock(
            side_effect=Exception("Database connection failed")
        )

        with pytest.raises(Exception, match="Database connection failed"):
            get_access_permissions(
                user_id=sample_user_id,
                community_id=sample_community_id,
                service=access_service,
            )
