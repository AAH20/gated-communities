"""Comprehensive agent tests for member verification in gated communities."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.gated_communities.agents.member_verification import (
    verify_member,
    get_verification_status,
    request_verification,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Provide a mock database connection."""
    db = Mock()
    db.execute = Mock()
    db.fetchone = Mock()
    db.fetchall = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def mock_community():
    """Provide a mock community object."""
    community = Mock()
    community.id = "comm_123"
    community.name = "Test Community"
    community.verification_required = True
    community.verification_threshold = 0.8
    return community


@pytest.fixture
def mock_member():
    """Provide a mock member object."""
    member = Mock()
    member.id = "user_456"
    member.community_id = "comm_123"
    member.username = "testuser"
    member.email = "test@example.com"
    member.is_verified = False
    member.verification_score = 0.0
    member.verification_date = None
    member.created_at = datetime.now() - timedelta(days=30)
    return member


@pytest.fixture
def mock_verified_member():
    """Provide a mock verified member object."""
    member = Mock()
    member.id = "user_789"
    member.community_id = "comm_123"
    member.username = "verified_user"
    member.email = "verified@example.com"
    member.is_verified = True
    member.verification_score = 0.95
    member.verification_date = datetime.now() - timedelta(days=10)
    member.created_at = datetime.now() - timedelta(days=60)
    return member


@pytest.fixture
def mock_verification_request():
    """Provide a mock verification request."""
    request = Mock()
    request.id = "req_001"
    request.member_id = "user_456"
    request.community_id = "comm_123"
    request.status = "pending"
    request.submitted_at = datetime.now() - timedelta(days=2)
    request.reviewed_at = None
    request.reviewed_by = None
    request.notes = ""
    return request


@pytest.fixture
def mock_notification_service():
    """Provide a mock notification service."""
    service = Mock()
    service.send = Mock(return_value=True)
    service.send_bulk = Mock(return_value=True)
    return service


@pytest.fixture
def mock_verification_service():
    """Provide a mock verification service."""
    service = Mock()
    service.check_identity = Mock(return_value={"score": 0.85, "status": "verified"})
    service.validate_documents = Mock(return_value={"valid": True, "score": 0.9})
    service.calculate_trust_score = Mock(return_value=0.88)
    return service


# ---------------------------------------------------------------------------
# Tests for verify_member
# ---------------------------------------------------------------------------


class TestVerifyMember:
    """Tests for the verify_member function."""

    def test_verify_member_success(
        self, mock_db, mock_member, mock_verification_service
    ):
        """Test successful member verification."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
        }
        mock_db.execute.return_value = Mock(rowcount=1)

        result = verify_member(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
            verification_service=mock_verification_service,
        )

        assert result is not None
        assert result["member_id"] == "user_456"
        assert result["community_id"] == "comm_123"
        assert result["is_verified"] is True
        assert "verification_date" in result
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()

    def test_verify_member_already_verified(
        self, mock_db, mock_verified_member
    ):
        """Test verification of an already verified member."""
        mock_db.fetchone.return_value = {
            "id": "user_789",
            "community_id": "comm_123",
            "is_verified": True,
        }

        result = verify_member(
            db=mock_db,
            member_id="user_789",
            community_id="comm_123",
        )

        assert result is not None
        assert result["is_verified"] is True
        assert result["message"] == "Member is already verified"

    def test_verify_member_not_found(self, mock_db):
        """Test verification when member does not exist."""
        mock_db.fetchone.return_value = None

        with pytest.raises(ValueError, match="Member not found"):
            verify_member(
                db=mock_db,
                member_id="nonexistent",
                community_id="comm_123",
            )

    def test_verify_member_wrong_community(self, mock_db, mock_member):
        """Test verification when member belongs to a different community."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_999",
            "is_verified": False,
        }

        with pytest.raises(
            ValueError, match="Member does not belong to this community"
        ):
            verify_member(
                db=mock_db,
                member_id="user_456",
                community_id="comm_123",
            )

    def test_verify_member_with_custom_score(
        self, mock_db, mock_member, mock_verification_service
    ):
        """Test verification with a custom verification score."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
        }
        mock_db.execute.return_value = Mock(rowcount=1)

        result = verify_member(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
            verification_service=mock_verification_service,
            custom_score=0.92,
        )

        assert result is not None
        assert result["verification_score"] == 0.92

    def test_verify_member_database_error(self, mock_db):
        """Test handling of database errors during verification."""
        mock_db.execute.side_effect = Exception("Database connection lost")

        with pytest.raises(Exception, match="Database connection lost"):
            verify_member(
                db=mock_db,
                member_id="user_456",
                community_id="comm_123",
            )

        mock_db.rollback.assert_called_once()

    def test_verify_member_sends_notification(
        self, mock_db, mock_member, mock_notification_service
    ):
        """Test that verification sends a notification to the member."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
        }
        mock_db.execute.return_value = Mock(rowcount=1)

        verify_member(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
            notification_service=mock_notification_service,
        )

        mock_notification_service.send.assert_called_once()
        call_args = mock_notification_service.send.call_args
        assert call_args[1]["user_id"] == "user_456"
        assert "verified" in call_args[1]["message"].lower()

    def test_verify_member_without_notification_service(
        self, mock_db, mock_member
    ):
        """Test verification works without a notification service."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
        }
        mock_db.execute.return_value = Mock(rowcount=1)

        result = verify_member(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
            notification_service=None,
        )

        assert result is not None
        assert result["is_verified"] is True

    def test_verify_member_updates_verification_date(
        self, mock_db, mock_member
    ):
        """Test that verification updates the verification date."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
        }
        mock_db.execute.return_value = Mock(rowcount=1)

        before = datetime.now()
        result = verify_member(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
        )
        after = datetime.now()

        assert result is not None
        assert before <= result["verification_date"] <= after

    def test_verify_member_with_notes(self, mock_db, mock_member):
        """Test verification with admin notes."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
        }
        mock_db.execute.return_value = Mock(rowcount=1)

        result = verify_member(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
            notes="Manual review completed",
        )

        assert result is not None
        assert result["notes"] == "Manual review completed"


# ---------------------------------------------------------------------------
# Tests for get_verification_status
# ---------------------------------------------------------------------------


class TestGetVerificationStatus:
    """Tests for the get_verification_status function."""

    def test_get_verification_status_verified(
        self, mock_db, mock_verified_member
    ):
        """Test getting status for a verified member."""
        mock_db.fetchone.return_value = {
            "id": "user_789",
            "community_id": "comm_123",
            "is_verified": True,
            "verification_score": 0.95,
            "verification_date": datetime.now() - timedelta(days=10),
        }

        result = get_verification_status(
            db=mock_db,
            member_id="user_789",
            community_id="comm_123",
        )

        assert result is not None
        assert result["member_id"] == "user_789"
        assert result["is_verified"] is True
        assert result["verification_score"] == 0.95
        assert result["status"] == "verified"

    def test_get_verification_status_unverified(
        self, mock_db, mock_member
    ):
        """Test getting status for an unverified member."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
            "verification_score": 0.0,
            "verification_date": None,
        }

        result = get_verification_status(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
        )

        assert result is not None
        assert result["member_id"] == "user_456"
        assert result["is_verified"] is False
        assert result["status"] == "unverified"

    def test_get_verification_status_pending(
        self, mock_db, mock_member, mock_verification_request
    ):
        """Test getting status for a member with a pending request."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
            "verification_score": 0.0,
            "verification_date": None,
        }
        mock_db.fetchall.return_value = [
            {
                "id": "req_001",
                "status": "pending",
                "submitted_at": datetime.now() - timedelta(days=2),
            }
        ]

        result = get_verification_status(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
        )

        assert result is not None
        assert result["status"] == "pending"
        assert "pending_request" in result

    def test_get_verification_status_member_not_found(self, mock_db):
        """Test getting status when member does not exist."""
        mock_db.fetchone.return_value = None

        with pytest.raises(ValueError, match="Member not found"):
            get_verification_status(
                db=mock_db,
                member_id="nonexistent",
                community_id="comm_123",
            )

    def test_get_verification_status_wrong_community(self, mock_db):
        """Test getting status when member belongs to a different community."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_999",
            "is_verified": False,
        }

        with pytest.raises(
            ValueError, match="Member does not belong to this community"
        ):
            get_verification_status(
                db=mock_db,
                member_id="user_456",
                community_id="comm_123",
            )

    def test_get_verification_status_includes_history(
        self, mock_db, mock_verified_member
    ):
        """Test that status includes verification history."""
        mock_db.fetchone.return_value = {
            "id": "user_789",
            "community_id": "comm_123",
            "is_verified": True,
            "verification_score": 0.95,
            "verification_date": datetime.now() - timedelta(days=10),
        }
        mock_db.fetchall.return_value = [
            {
                "action": "verified",
                "timestamp": datetime.now() - timedelta(days=10),
                "score": 0.95,
            }
        ]

        result = get_verification_status(
            db=mock_db,
            member_id="user_789",
            community_id="comm_123",
            include_history=True,
        )

        assert result is not None
        assert "history" in result
        assert len(result["history"]) > 0

    def test_get_verification_status_without_history(
        self, mock_db, mock_verified_member
    ):
        """Test that status excludes history when not requested."""
        mock_db.fetchone.return_value = {
            "id": "user_789",
            "community_id": "comm_123",
            "is_verified": True,
            "verification_score": 0.95,
            "verification_date": datetime.now() - timedelta(days=10),
        }

        result = get_verification_status(
            db=mock_db,
            member_id="user_789",
            community_id="comm_123",
            include_history=False,
        )

        assert result is not None
        assert "history" not in result

    def test_get_verification_status_database_error(self, mock_db):
        """Test handling of database errors."""
        mock_db.execute.side_effect = Exception("Database connection lost")

        with pytest.raises(Exception, match="Database connection lost"):
            get_verification_status(
                db=mock_db,
                member_id="user_456",
                community_id="comm_123",
            )

    def test_get_verification_status_rejected(
        self, mock_db, mock_member
    ):
        """Test getting status for a member with a rejected request."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
            "verification_score": 0.0,
            "verification_date": None,
        }
        mock_db.fetchall.return_value = [
            {
                "id": "req_001",
                "status": "rejected",
                "submitted_at": datetime.now() - timedelta(days=5),
                "reviewed_at": datetime.now() - timedelta(days=3),
            }
        ]

        result = get_verification_status(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
        )

        assert result is not None
        assert result["status"] == "rejected"
        assert "rejection_reason" in result or "last_request" in result


# ---------------------------------------------------------------------------
# Tests for request_verification
# ---------------------------------------------------------------------------


class TestRequestVerification:
    """Tests for the request_verification function."""

    def test_request_verification_success(
        self, mock_db, mock_member, mock_verification_service
    ):
        """Test successful verification request submission."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
        }
        mock_db.execute.return_value = Mock(rowcount=1)

        result = request_verification(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
            verification_service=mock_verification_service,
        )

        assert result is not None
        assert result["member_id"] == "user_456"
        assert result["community_id"] == "comm_123"
        assert result["status"] == "pending"
        assert "request_id" in result
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()

    def test_request_verification_already_verified(
        self, mock_db, mock_verified_member
    ):
        """Test request when member is already verified."""
        mock_db.fetchone.return_value = {
            "id": "user_789",
            "community_id": "comm_123",
            "is_verified": True,
        }

        result = request_verification(
            db=mock_db,
            member_id="user_789",
            community_id="comm_123",
        )

        assert result is not None
        assert result["status"] == "already_verified"

    def test_request_verification_pending_exists(
        self, mock_db, mock_member, mock_verification_request
    ):
        """Test request when a pending request already exists."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
        }
        mock_db.fetchall.return_value = [
            {
                "id": "req_001",
                "status": "pending",
                "submitted_at": datetime.now() - timedelta(days=1),
            }
        ]

        result = request_verification(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
        )

        assert result is not None
        assert result["status"] == "pending"
        assert result["message"] == "Verification request already pending"

    def test_request_verification_member_not_found(self, mock_db):
        """Test request when member does not exist."""
        mock_db.fetchone.return_value = None

        with pytest.raises(ValueError, match="Member not found"):
            request_verification(
                db=mock_db,
                member_id="nonexistent",
                community_id="comm_123",
            )

    def test_request_verification_wrong_community(self, mock_db):
        """Test request when member belongs to a different community."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_999",
            "is_verified": False,
        }

        with pytest.raises(
            ValueError, match="Member does not belong to this community"
        ):
            request_verification(
                db=mock_db,
                member_id="user_456",
                community_id="comm_123",
            )

    def test_request_verification_with_documents(
        self, mock_db, mock_member, mock_verification_service
    ):
        """Test request with document upload."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
        }
        mock_db.execute.return_value = Mock(rowcount=1)

        documents = [
            {"type": "id", "url": "https://example.com/id.pdf"},
            {"type": "proof_of_address", "url": "https://example.com/address.pdf"},
        ]

        result = request_verification(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
            verification_service=mock_verification_service,
            documents=documents,
        )

        assert result is not None
        assert result["status"] == "pending"
        assert "documents" in result
        assert len(result["documents"]) == 2

    def test_request_verification_database_error(self, mock_db):
        """Test handling of database errors during request."""
        mock_db.execute.side_effect = Exception("Database connection lost")

        with pytest.raises(Exception, match="Database connection lost"):
            request_verification(
                db=mock_db,
                member_id="user_456",
                community_id="comm_123",
            )

        mock_db.rollback.assert_called_once()

    def test_request_verification_sends_notification(
        self, mock_db, mock_member, mock_notification_service
    ):
        """Test that request sends a notification."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
        }
        mock_db.execute.return_value = Mock(rowcount=1)

        request_verification(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
            notification_service=mock_notification_service,
        )

        mock_notification_service.send.assert_called_once()
        call_args = mock_notification_service.send.call_args
        assert call_args[1]["user_id"] == "user_456"
        assert "request" in call_args[1]["message"].lower()

    def test_request_verification_without_notification_service(
        self, mock_db, mock_member
    ):
        """Test request works without a notification service."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
        }
        mock_db.execute.return_value = Mock(rowcount=1)

        result = request_verification(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
            notification_service=None,
        )

        assert result is not None
        assert result["status"] == "pending"

    def test_request_verification_with_notes(self, mock_db, mock_member):
        """Test request with additional notes."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
        }
        mock_db.execute.return_value = Mock(rowcount=1)

        result = request_verification(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
            notes="Please verify my account as soon as possible",
        )

        assert result is not None
        assert result["status"] == "pending"
        assert result["notes"] == "Please verify my account as soon as possible"

    def test_request_verification_rate_limited(
        self, mock_db, mock_member
    ):
        """Test request is rate limited for recent requests."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
        }
        mock_db.fetchall.return_value = [
            {
                "id": "req_001",
                "status": "rejected",
                "submitted_at": datetime.now() - timedelta(hours=1),
                "reviewed_at": datetime.now() - timedelta(minutes=30),
            }
        ]

        result = request_verification(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
        )

        assert result is not None
        assert result["status"] == "rate_limited"
        assert "retry_after" in result

    def test_request_verification_auto_approve_high_trust(
        self, mock_db, mock_member, mock_verification_service
    ):
        """Test auto-approval for high-trust members."""
        mock_db.fetchone.return_value = {
            "id": "user_456",
            "community_id": "comm_123",
            "is_verified": False,
        }
        mock_verification_service.calculate_trust_score.return_value = 0.98
        mock_db.execute.return_value = Mock(rowcount=1)

        result = request_verification(
            db=mock_db,
            member_id="user_456",
            community_id="comm_123",
            verification_service=mock_verification_service,
            auto_approve_threshold=0.95,
        )

        assert result is not None
        assert result["status"] == "approved"
        assert result["is_verified"] is True
