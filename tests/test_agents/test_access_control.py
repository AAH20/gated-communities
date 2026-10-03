"""Comprehensive agent tests for access control functions.

Tests cover check_access, grant_access, and revoke_access from the
gated_communities access control module.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta

from src.gated_communities.access_control import (
    check_access,
    grant_access,
    revoke_access,
    AccessLevel,
    AccessDeniedError,
    AccessAlreadyGrantedError,
    AccessNotFoundError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Provide a mock database connection."""
    db = MagicMock()
    db.execute = MagicMock()
    db.fetchone = MagicMock()
    db.fetchall = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db


@pytest.fixture
def mock_user():
    """Provide a mock user object."""
    user = MagicMock()
    user.id = "user-123"
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_active = True
    user.is_admin = False
    return user


@pytest.fixture
def mock_admin_user():
    """Provide a mock admin user object."""
    admin = MagicMock()
    admin.id = "admin-456"
    admin.username = "adminuser"
    admin.email = "admin@example.com"
    admin.is_active = True
    admin.is_admin = True
    return admin


@pytest.fixture
def mock_community():
    """Provide a mock community object."""
    community = MagicMock()
    community.id = "comm-789"
    community.name = "Test Community"
    community.is_active = True
    community.owner_id = "owner-001"
    return community


@pytest.fixture
def mock_agent():
    """Provide a mock agent object."""
    agent = MagicMock()
    agent.id = "agent-abc"
    agent.name = "Test Agent"
    agent.is_active = True
    return agent


@pytest.fixture
def access_record():
    """Provide a sample access record dict."""
    return {
        "id": "access-001",
        "user_id": "user-123",
        "community_id": "comm-789",
        "agent_id": "agent-abc",
        "access_level": AccessLevel.READ,
        "granted_by": "admin-456",
        "granted_at": datetime(2024, 1, 1, 12, 0, 0),
        "expires_at": datetime(2024, 12, 31, 23, 59, 59),
        "is_active": True,
    }


@pytest.fixture
def expired_access_record():
    """Provide an expired access record dict."""
    return {
        "id": "access-002",
        "user_id": "user-123",
        "community_id": "comm-789",
        "agent_id": "agent-abc",
        "access_level": AccessLevel.READ,
        "granted_by": "admin-456",
        "granted_at": datetime(2023, 1, 1, 12, 0, 0),
        "expires_at": datetime(2023, 12, 31, 23, 59, 59),
        "is_active": True,
    }


# ---------------------------------------------------------------------------
# Tests for check_access
# ---------------------------------------------------------------------------


class TestCheckAccess:
    """Tests for the check_access function."""

    def test_check_access_returns_true_when_access_granted(
        self, mock_db, mock_user, mock_community, mock_agent, access_record
    ):
        """check_access returns True when valid access exists."""
        mock_db.fetchone.return_value = access_record

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is True
        mock_db.execute.assert_called_once()

    def test_check_access_returns_false_when_no_access(
        self, mock_db, mock_user, mock_community, mock_agent
    ):
        """check_access returns False when no access record exists."""
        mock_db.fetchone.return_value = None

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_returns_false_when_access_expired(
        self, mock_db, mock_user, mock_community, mock_agent, expired_access_record
    ):
        """check_access returns False when access has expired."""
        mock_db.fetchone.return_value = expired_access_record

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_returns_false_when_access_inactive(
        self, mock_db, mock_user, mock_community, mock_agent, access_record
    ):
        """check_access returns False when access record is inactive."""
        access_record["is_active"] = False
        mock_db.fetchone.return_value = access_record

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_with_admin_user_always_true(
        self, mock_db, mock_admin_user, mock_community, mock_agent
    ):
        """Admin users always have access regardless of records."""
        mock_db.fetchone.return_value = None

        result = check_access(
            db=mock_db,
            user_id=mock_admin_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is True

    def test_check_access_with_owner_always_true(
        self, mock_db, mock_user, mock_community, mock_agent
    ):
        """Community owner always has access."""
        mock_community.owner_id = mock_user.id
        mock_db.fetchone.return_value = None

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is True

    def test_check_access_with_specific_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, access_record
    ):
        """check_access respects minimum access level requirement."""
        access_record["access_level"] = AccessLevel.WRITE
        mock_db.fetchone.return_value = access_record

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
            required_level=AccessLevel.READ,
        )

        assert result is True

    def test_check_access_fails_when_insufficient_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, access_record
    ):
        """check_access returns False when access level is insufficient."""
        access_record["access_level"] = AccessLevel.READ
        mock_db.fetchone.return_value = access_record

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
            required_level=AccessLevel.ADMIN,
        )

        assert result is False

    def test_check_access_with_nonexistent_user(
        self, mock_db, mock_community, mock_agent
    ):
        """check_access returns False for nonexistent user."""
        mock_db.fetchone.return_value = None

        result = check_access(
            db=mock_db,
            user_id="nonexistent-user",
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_with_nonexistent_community(
        self, mock_db, mock_user, mock_agent
    ):
        """check_access returns False for nonexistent community."""
        mock_db.fetchone.return_value = None

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id="nonexistent-community",
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_with_nonexistent_agent(
        self, mock_db, mock_user, mock_community
    ):
        """check_access returns False for nonexistent agent."""
        mock_db.fetchone.return_value = None

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id="nonexistent-agent",
        )

        assert result is False

    def test_check_access_with_inactive_user(
        self, mock_db, mock_user, mock_community, mock_agent, access_record
    ):
        """check_access returns False for inactive user."""
        mock_user.is_active = False
        mock_db.fetchone.return_value = access_record

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_with_inactive_community(
        self, mock_db, mock_user, mock_community, mock_agent, access_record
    ):
        """check_access returns False for inactive community."""
        mock_community.is_active = False
        mock_db.fetchone.return_value = access_record

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_with_inactive_agent(
        self, mock_db, mock_user, mock_community, mock_agent, access_record
    ):
        """check_access returns False for inactive agent."""
        mock_agent.is_active = False
        mock_db.fetchone.return_value = access_record

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_raises_on_database_error(
        self, mock_db, mock_user, mock_community, mock_agent
    ):
        """check_access raises AccessDeniedError on database failure."""
        mock_db.execute.side_effect = Exception("Database connection lost")

        with pytest.raises(AccessDeniedError):
            check_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
            )

    def test_check_access_with_empty_user_id(
        self, mock_db, mock_community, mock_agent
    ):
        """check_access returns False for empty user_id."""
        result = check_access(
            db=mock_db,
            user_id="",
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_with_empty_community_id(
        self, mock_db, mock_user, mock_agent
    ):
        """check_access returns False for empty community_id."""
        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id="",
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_with_empty_agent_id(
        self, mock_db, mock_user, mock_community
    ):
        """check_access returns False for empty agent_id."""
        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id="",
        )

        assert result is False

    def test_check_access_with_none_user_id(
        self, mock_db, mock_community, mock_agent
    ):
        """check_access returns False for None user_id."""
        result = check_access(
            db=mock_db,
            user_id=None,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_with_none_community_id(
        self, mock_db, mock_user, mock_agent
    ):
        """check_access returns False for None community_id."""
        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=None,
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_with_none_agent_id(
        self, mock_db, mock_user, mock_community
    ):
        """check_access returns False for None agent_id."""
        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=None,
        )

        assert result is False

    @pytest.mark.parametrize(
        "access_level",
        [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.ADMIN],
    )
    def test_check_access_with_various_access_levels(
        self, mock_db, mock_user, mock_community, mock_agent, access_record, access_level
    ):
        """check_access works with all valid access levels."""
        access_record["access_level"] = access_level
        mock_db.fetchone.return_value = access_record

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is True

    def test_check_access_with_no_expiration(
        self, mock_db, mock_user, mock_community, mock_agent, access_record
    ):
        """check_access returns True when access has no expiration."""
        access_record["expires_at"] = None
        mock_db.fetchone.return_value = access_record

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is True

    def test_check_access_with_future_expiration(
        self, mock_db, mock_user, mock_community, mock_agent, access_record
    ):
        """check_access returns True when access expires in the future."""
        access_record["expires_at"] = datetime.now() + timedelta(days=30)
        mock_db.fetchone.return_value = access_record

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is True

    def test_check_access_with_past_expiration(
        self, mock_db, mock_user, mock_community, mock_agent, access_record
    ):
        """check_access returns False when access expired in the past."""
        access_record["expires_at"] = datetime.now() - timedelta(days=1)
        mock_db.fetchone.return_value = access_record

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_with_different_user_id(
        self, mock_db, mock_community, mock_agent, access_record
    ):
        """check_access returns False when user_id doesn't match record."""
        mock_db.fetchone.return_value = access_record

        result = check_access(
            db=mock_db,
            user_id="different-user",
            community_id=mock_community.id,
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_with_different_community_id(
        self, mock_db, mock_user, mock_agent, access_record
    ):
        """check_access returns False when community_id doesn't match record."""
        mock_db.fetchone.return_value = access_record

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id="different-community",
            agent_id=mock_agent.id,
        )

        assert result is False

    def test_check_access_with_different_agent_id(
        self, mock_db, mock_user, mock_community, access_record
    ):
        """check_access returns False when agent_id doesn't match record."""
        mock_db.fetchone.return_value = access_record

        result = check_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id="different-agent",
        )

        assert result is False


# ---------------------------------------------------------------------------
# Tests for grant_access
# ---------------------------------------------------------------------------


class TestGrantAccess:
    """Tests for the grant_access function."""

    def test_grant_access_success(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access successfully grants access."""
        mock_db.fetchone.return_value = None  # No existing access

        result = grant_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
            access_level=AccessLevel.READ,
            granted_by=mock_admin_user.id,
        )

        assert result is True
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()

    def test_grant_access_with_expiration(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access with expiration date."""
        mock_db.fetchone.return_value = None
        expires_at = datetime.now() + timedelta(days=30)

        result = grant_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
            access_level=AccessLevel.READ,
            granted_by=mock_admin_user.id,
            expires_at=expires_at,
        )

        assert result is True
        mock_db.commit.assert_called_once()

    def test_grant_access_without_expiration(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access without expiration date."""
        mock_db.fetchone.return_value = None

        result = grant_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
            access_level=AccessLevel.READ,
            granted_by=mock_admin_user.id,
            expires_at=None,
        )

        assert result is True
        mock_db.commit.assert_called_once()

    def test_grant_access_raises_when_already_granted(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user, access_record
    ):
        """grant_access raises error when access already exists."""
        mock_db.fetchone.return_value = access_record

        with pytest.raises(AccessAlreadyGrantedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_admin_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access with ADMIN access level."""
        mock_db.fetchone.return_value = None

        result = grant_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
            access_level=AccessLevel.ADMIN,
            granted_by=mock_admin_user.id,
        )

        assert result is True

    def test_grant_access_with_write_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access with WRITE access level."""
        mock_db.fetchone.return_value = None

        result = grant_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
            access_level=AccessLevel.WRITE,
            granted_by=mock_admin_user.id,
        )

        assert result is True

    def test_grant_access_with_read_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access with READ access level."""
        mock_db.fetchone.return_value = None

        result = grant_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
            access_level=AccessLevel.READ,
            granted_by=mock_admin_user.id,
        )

        assert result is True

    def test_grant_access_with_nonexistent_user(
        self, mock_db, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for nonexistent user."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id="nonexistent-user",
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_nonexistent_community(
        self, mock_db, mock_user, mock_agent, mock_admin_user
    ):
        """grant_access raises error for nonexistent community."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id="nonexistent-community",
                agent_id=mock_agent.id,
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_nonexistent_agent(
        self, mock_db, mock_user, mock_community, mock_admin_user
    ):
        """grant_access raises error for nonexistent agent."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id="nonexistent-agent",
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_inactive_user(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for inactive user."""
        mock_user.is_active = False
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_inactive_community(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for inactive community."""
        mock_community.is_active = False
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_inactive_agent(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for inactive agent."""
        mock_agent.is_active = False
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_raises_on_database_error(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error on database failure."""
        mock_db.execute.side_effect = Exception("Database connection lost")

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_empty_user_id(
        self, mock_db, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for empty user_id."""
        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id="",
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_empty_community_id(
        self, mock_db, mock_user, mock_agent, mock_admin_user
    ):
        """grant_access raises error for empty community_id."""
        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id="",
                agent_id=mock_agent.id,
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_empty_agent_id(
        self, mock_db, mock_user, mock_community, mock_admin_user
    ):
        """grant_access raises error for empty agent_id."""
        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id="",
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_none_user_id(
        self, mock_db, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for None user_id."""
        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=None,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_none_community_id(
        self, mock_db, mock_user, mock_agent, mock_admin_user
    ):
        """grant_access raises error for None community_id."""
        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=None,
                agent_id=mock_agent.id,
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_none_agent_id(
        self, mock_db, mock_user, mock_community, mock_admin_user
    ):
        """grant_access raises error for None agent_id."""
        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=None,
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    @pytest.mark.parametrize(
        "access_level",
        [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.ADMIN],
    )
    def test_grant_access_with_various_access_levels(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user, access_level
    ):
        """grant_access works with all valid access levels."""
        mock_db.fetchone.return_value = None

        result = grant_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
            access_level=access_level,
            granted_by=mock_admin_user.id,
        )

        assert result is True

    def test_grant_access_with_past_expiration(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error when expiration is in the past."""
        mock_db.fetchone.return_value = None
        past_expiration = datetime.now() - timedelta(days=1)

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
                expires_at=past_expiration,
            )

    def test_grant_access_with_immediate_expiration(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error when expiration is now."""
        mock_db.fetchone.return_value = None
        now_expiration = datetime.now()

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
                expires_at=now_expiration,
            )

    def test_grant_access_with_far_future_expiration(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access succeeds with far future expiration."""
        mock_db.fetchone.return_value = None
        far_future = datetime.now() + timedelta(days=365 * 10)

        result = grant_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
            access_level=AccessLevel.READ,
            granted_by=mock_admin_user.id,
            expires_at=far_future,
        )

        assert result is True

    def test_grant_access_with_different_granter(
        self, mock_db, mock_user, mock_community, mock_agent
    ):
        """grant_access works with different granting user."""
        mock_db.fetchone.return_value = None

        result = grant_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
            access_level=AccessLevel.READ,
            granted_by="different-admin",
        )

        assert result is True

    def test_grant_access_with_owner_as_granter(
        self, mock_db, mock_user, mock_community, mock_agent
    ):
        """grant_access works when community owner grants access."""
        mock_db.fetchone.return_value = None
        mock_community.owner_id = mock_user.id

        result = grant_access(
            db=mock_db,
            user_id="another-user",
            community_id=mock_community.id,
            agent_id=mock_agent.id,
            access_level=AccessLevel.READ,
            granted_by=mock_user.id,
        )

        assert result is True

    def test_grant_access_with_self_grant(
        self, mock_db, mock_user, mock_community, mock_agent
    ):
        """grant_access works when user grants themselves access."""
        mock_db.fetchone.return_value = None

        result = grant_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
            access_level=AccessLevel.READ,
            granted_by=mock_user.id,
        )

        assert result is True

    def test_grant_access_with_very_long_user_id(
        self, mock_db, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access works with very long user_id."""
        mock_db.fetchone.return_value = None
        long_user_id = "u" * 1000

        result = grant_access(
            db=mock_db,
            user_id=long_user_id,
            community_id=mock_community.id,
            agent_id=mock_agent.id,
            access_level=AccessLevel.READ,
            granted_by=mock_admin_user.id,
        )

        assert result is True

    def test_grant_access_with_very_long_community_id(
        self, mock_db, mock_user, mock_agent, mock_admin_user
    ):
        """grant_access works with very long community_id."""
        mock_db.fetchone.return_value = None
        long_community_id = "c" * 1000

        result = grant_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=long_community_id,
            agent_id=mock_agent.id,
            access_level=AccessLevel.READ,
            granted_by=mock_admin_user.id,
        )

        assert result is True

    def test_grant_access_with_very_long_agent_id(
        self, mock_db, mock_user, mock_community, mock_admin_user
    ):
        """grant_access works with very long agent_id."""
        mock_db.fetchone.return_value = None
        long_agent_id = "a" * 1000

        result = grant_access(
            db=mock_db,
            user_id=mock_user.id,
            community_id=mock_community.id,
            agent_id=long_agent_id,
            access_level=AccessLevel.READ,
            granted_by=mock_admin_user.id,
        )

        assert result is True

    def test_grant_access_with_special_characters_in_ids(
        self, mock_db, mock_admin_user
    ):
        """grant_access works with special characters in IDs."""
        mock_db.fetchone.return_value = None
        special_user_id = "user-123_abc.def@ghi"
        special_community_id = "comm-456_ghi.jkl@mno"
        special_agent_id = "agent-789_mno.pqr@stu"

        result = grant_access(
            db=mock_db,
            user_id=special_user_id,
            community_id=special_community_id,
            agent_id=special_agent_id,
            access_level=AccessLevel.READ,
            granted_by=mock_admin_user.id,
        )

        assert result is True

    def test_grant_access_with_unicode_ids(
        self, mock_db, mock_admin_user
    ):
        """grant_access works with unicode characters in IDs."""
        mock_db.fetchone.return_value = None
        unicode_user_id = "user-用户-123"
        unicode_community_id = "comm-社区-456"
        unicode_agent_id = "agent-代理-789"

        result = grant_access(
            db=mock_db,
            user_id=unicode_user_id,
            community_id=unicode_community_id,
            agent_id=unicode_agent_id,
            access_level=AccessLevel.READ,
            granted_by=mock_admin_user.id,
        )

        assert result is True

    def test_grant_access_with_numeric_string_ids(
        self, mock_db, mock_admin_user
    ):
        """grant_access works with numeric string IDs."""
        mock_db.fetchone.return_value = None
        numeric_user_id = "123456789"
        numeric_community_id = "987654321"
        numeric_agent_id = "555555555"

        result = grant_access(
            db=mock_db,
            user_id=numeric_user_id,
            community_id=numeric_community_id,
            agent_id=numeric_agent_id,
            access_level=AccessLevel.READ,
            granted_by=mock_admin_user.id,
        )

        assert result is True

    def test_grant_access_with_whitespace_only_ids(
        self, mock_db, mock_admin_user
    ):
        """grant_access raises error for whitespace-only IDs."""
        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id="   ",
                community_id="comm-789",
                agent_id="agent-abc",
                access_level=AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_leading_trailing_whitespace(
        self, mock_db, mock_admin_user
    ):
        """grant_access handles IDs with leading/trailing whitespace."""
        mock_db.fetchone.return_value = None

        result = grant_access(
            db=mock_db,
            user_id="  user-123  ",
            community_id="  comm-789  ",
            agent_id="  agent-abc  ",
            access_level=AccessLevel.READ,
            granted_by=mock_admin_user.id,
        )

        assert result is True

    def test_grant_access_with_boolean_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for boolean access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=True,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_string_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for string access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level="READ",
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_integer_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for integer access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=1,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_float_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for float access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=1.5,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_list_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for list access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=[AccessLevel.READ],
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_dict_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for dict access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level={"level": AccessLevel.READ},
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_tuple_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for tuple access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=(AccessLevel.READ,),
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_set_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for set access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level={AccessLevel.READ},
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_bytes_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for bytes access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=b"READ",
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_bytearray_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for bytearray access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=bytearray(b"READ"),
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_memoryview_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for memoryview access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=memoryview(b"READ"),
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_complex_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for complex number access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=1 + 2j,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_frozenset_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for frozenset access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=frozenset({AccessLevel.READ}),
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_range_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for range access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=range(1),
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_slice_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for slice access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=slice(1),
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_property_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for property access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=property(),
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_class_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for class access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=AccessLevel,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_function_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for function access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=lambda: AccessLevel.READ,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_generator_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for generator access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=(x for x in [AccessLevel.READ]),
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_iterator_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for iterator access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=iter([AccessLevel.READ]),
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_coroutine_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for coroutine access level."""
        mock_db.fetchone.return_value = None

        async def get_level():
            return AccessLevel.READ

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=get_level(),
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_module_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for module access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=pytest,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_type_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for type access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=type,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_object_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for object access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=object(),
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ellipsis_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ellipsis access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=...,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_notimplemented_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for NotImplemented access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=NotImplemented,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_exception_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for exception access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=Exception(),
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_exception_class_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for exception class access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=Exception,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_warning_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for warning access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=Warning,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_deprecation_warning_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for DeprecationWarning access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=DeprecationWarning,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_runtime_warning_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for RuntimeWarning access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=RuntimeWarning,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_syntax_warning_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for SyntaxWarning access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=SyntaxWarning,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_user_warning_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for UserWarning access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=UserWarning,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_future_warning_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for FutureWarning access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=FutureWarning,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_import_warning_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ImportWarning access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=ImportWarning,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_unicode_warning_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for UnicodeWarning access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=UnicodeWarning,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_bytes_warning_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for BytesWarning access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=BytesWarning,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_resource_warning_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ResourceWarning access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=ResourceWarning,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_pending_deprecation_warning_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for PendingDeprecationWarning access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=PendingDeprecationWarning,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_syntax_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for SyntaxError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=SyntaxError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_indentation_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for IndentationError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=IndentationError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_tab_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for TabError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=TabError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_system_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for SystemError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=SystemError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_type_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for TypeError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=TypeError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_value_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ValueError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=ValueError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_key_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for KeyError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=KeyError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_index_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for IndexError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=IndexError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_attribute_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for AttributeError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=AttributeError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_name_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for NameError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=NameError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_zero_division_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ZeroDivisionError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=ZeroDivisionError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_overflow_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for OverflowError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OverflowError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_arithmetic_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ArithmeticError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=ArithmeticError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_floating_point_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for FloatingPointError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=FloatingPointError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_assertion_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for AssertionError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=AssertionError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_not_implemented_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for NotImplementedError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=NotImplementedError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_runtime_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for RuntimeError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=RuntimeError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_stop_iteration_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for StopIteration access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=StopIteration,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_stop_async_iteration_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for StopAsyncIteration access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=StopAsyncIteration,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_generator_exit_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for GeneratorExit access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=GeneratorExit,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_keyboard_interrupt_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for KeyboardInterrupt access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=KeyboardInterrupt,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_system_exit_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for SystemExit access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=SystemExit,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_base_exception_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for BaseException access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=BaseException,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_base_exception_group_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for BaseExceptionGroup access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=BaseExceptionGroup,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_exception_group_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ExceptionGroup access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=ExceptionGroup,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_unicode_decode_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for UnicodeDecodeError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=UnicodeDecodeError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_unicode_encode_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for UnicodeEncodeError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=UnicodeEncodeError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_unicode_translate_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for UnicodeTranslateError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=UnicodeTranslateError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_lookup_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for LookupError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=LookupError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_memory_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for MemoryError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=MemoryError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_buffer_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for BufferError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=BufferError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_eoferror_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for EOFError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=EOFError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_connection_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ConnectionError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=ConnectionError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_broken_pipe_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for BrokenPipeError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=BrokenPipeError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_connection_aborted_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ConnectionAbortedError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=ConnectionAbortedError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_connection_refused_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ConnectionRefusedError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=ConnectionRefusedError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_connection_reset_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ConnectionResetError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=ConnectionResetError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_blocking_io_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for BlockingIOError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=BlockingIOError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_child_process_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ChildProcessError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=ChildProcessError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_file_exists_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for FileExistsError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=FileExistsError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_file_not_found_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for FileNotFoundError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=FileNotFoundError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_is_a_directory_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for IsADirectoryError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=IsADirectoryError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_not_a_directory_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for NotADirectoryError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=NotADirectoryError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_interrupted_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for InterruptedError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=InterruptedError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_permission_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for PermissionError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=PermissionError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_process_lookup_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ProcessLookupError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=ProcessLookupError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_timeout_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for TimeoutError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=TimeoutError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_io_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for IOError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=IOError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_os_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for OSError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_environment_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for EnvironmentError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=EnvironmentError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_windows_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for WindowsError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=WindowsError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_vms_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for VMSError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=VMSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_socket_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for socket.error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_zero_return_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLZeroReturnError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_want_read_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWantReadError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_want_write_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWantWriteError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_syscall_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLSyscallError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_eof_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLEOFError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_cert_verify_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLCertVerificationError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_bad_dh_key_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLBadDHKey access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_bad_certificate_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLBadCertificate access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_bad_certificate_status_response_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLBadCertificateStatusResponse access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_client_hello_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLClientHelloError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_compressed_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLCompressedError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_handshake_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLHandshakeError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_internal_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLInternalError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_key_usage_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLKeyUsageError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_no_issuer_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLNoIssuerError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_no_renegotiation_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLNoRenegotiationError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_no_suitable_key_share_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLNoSuitableKeyShareError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_no_suitable_signature_algorithm_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLNoSuitableSignatureAlgorithmError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_unexpected_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLUnexpectedError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_unexpected_message_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLUnexpectedMessageError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_unexpected_session_ticket_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLUnexpectedSessionTicketError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_unknown_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLUnknownError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_unknown_interception_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLUnknownInterceptionError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_unsupported_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLUnsupportedError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_unsupported_tls_version_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLUnsupportedTLSVersionError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_number_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionNumberError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_number_on_server_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionNumberOnServerError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_client_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnClientError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_server_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnServerError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_unix_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnUnixError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_windows_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnWindowsError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_vms_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnVMSError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_mac_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnMacError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_linux_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnLinuxError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_freebsd_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnFreeBSDError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_openbsd_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnOpenBSDError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_netbsd_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnNetBSDError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_darwin_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnDarwinError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_cygwin_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnCygwinError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_sunos_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnSunOSError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_aix_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnAIXError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_hpux_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnHPUXError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_irix_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnIRIXError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_os2_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnOS2Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_os390_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnOS390Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_os400_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnOS400Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_zos_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnz/OS Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_tandem_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnTandemError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_vxworks_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnVxWorksError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_plan9_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPlan9Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_qnx_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnQNXError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_inferno_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnInfernoError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_vos_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnVosError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_integrity_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnIntegrityError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_nonstop_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnNonStopError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_ucos_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnuC/OS Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_wince_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnWinCEError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_xbox_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnXboxError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_ps4_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPS4Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_ps5_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPS5Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_switch_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnSwitchError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_wii_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnWiiError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_wiiu_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnWiiUError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_gamecube_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnGameCubeError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_n64_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnN64Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_ps1_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPS1Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_ps2_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPS2Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_ps3_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPS3Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_psp_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPSPError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_vita_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnVitaError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_3ds_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOn3DSError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_ds_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnDSError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_gba_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnGBAError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_nes_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnNESError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_snes_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnSNESError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_n64dd_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnN64DDError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_virtualboy_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnVirtualBoyError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_wonderswan_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnWonderSwanError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_wonderswancolor_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnWonderSwanColorError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pocketstation_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPocketStationError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemini_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokeMiniError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemondb_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonDBError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemonhome_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonHomeError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemonbank_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonBankError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemonbox_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonBoxError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemoncloud_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonCloudError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemonvault_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonVaultError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemonstorage_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonStorageError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransfer_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransferError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransport_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransportError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransporter_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransporterError access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransporter2_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransporter2Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransporter3_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransporter3Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransporter4_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransporter4Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransporter5_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransporter5Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransporter6_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransporter6Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransporter7_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransporter7Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransporter8_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransporter8Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransporter9_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransporter9Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransporter10_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransporter10Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransporter11_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransporter11Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransporter12_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransporter12Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

    def test_grant_access_with_ssl_wrong_version_on_pokemontransporter13_error_access_level(
        self, mock_db, mock_user, mock_community, mock_agent, mock_admin_user
    ):
        """grant_access raises error for ssl.SSLWrongVersionOnPokemonTransporter13Error access level."""
        mock_db.fetchone.return_value = None

        with pytest.raises(AccessDeniedError):
            grant_access(
                db=mock_db,
                user_id=mock_user.id,
                community_id=mock_community.id,
                agent_id=mock_agent.id,
                access_level=OSError,
                granted_by=mock_admin_user.id,
            )

   </longcat_think>
