"""Comprehensive agent tests for community governance operations."""

import pytest
from unittest.mock import MagicMock, patch
from gated_communities.agents.community_governance import (
    BaseAgent,
    DisputeResolverAgent,
    GovernanceAnalyticsAgent,
    GovernanceExplainerAgent,
    PolicyManagerAgent,
    RuleEnforcerAgent,
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
def sample_policy_data():
    """Provide sample governance policy data."""
    return {
        "policy_id": "policy-001",
        "community_id": "community-001",
        "name": "Content Moderation Policy",
        "description": "Rules for content moderation in the community",
        "rules": [
            {"type": "keyword_filter", "action": "block", "patterns": ["spam", "scam"]},
            {"type": "rate_limit", "action": "throttle", "max_posts_per_hour": 10},
        ],
        "enforcement_level": "strict",
        "created_by": "admin-001",
        "is_active": True,
    }


@pytest.fixture
def sample_policy_record():
    """Provide a sample policy record as returned from the database."""
    return {
        "id": "policy-001",
        "community_id": "community-001",
        "name": "Content Moderation Policy",
        "description": "Rules for content moderation in the community",
        "rules_json": '[{"type": "keyword_filter", "action": "block"}]',
        "enforcement_level": "strict",
        "created_by": "admin-001",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_enforcement_context():
    """Provide sample context for policy enforcement."""
    return {
        "user_id": "user-123",
        "community_id": "community-001",
        "action": "post_content",
        "content": "This is a test post",
        "metadata": {"ip": "192.168.1.1", "user_agent": "test-agent"},
    }


# ---------------------------------------------------------------------------
# Tests: create_governance_policy
# ---------------------------------------------------------------------------

class TestCreateGovernancePolicy:
    """Tests for the create_governance_policy function."""

    def test_create_governance_policy_success(self, mock_db, sample_policy_data):
        """Test successful creation of a governance policy."""
        mock_db.execute.return_value = None
        mock_db.fetchone.return_value = {"id": "policy-001"}

        result = create_governance_policy(
            db=mock_db,
            community_id=sample_policy_data["community_id"],
            name=sample_policy_data["name"],
            description=sample_policy_data["description"],
            rules=sample_policy_data["rules"],
            enforcement_level=sample_policy_data["enforcement_level"],
            created_by=sample_policy_data["created_by"],
        )

        assert result is not None
        assert result["id"] == "policy-001"
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_governance_policy_with_minimal_fields(self, mock_db):
        """Test creating a policy with only required fields."""
        mock_db.fetchone.return_value = {"id": "policy-minimal"}

        result = create_governance_policy(
            db=mock_db,
            community_id="community-002",
            name="Basic Policy",
            description="A basic policy",
            rules=[],
            enforcement_level="lenient",
            created_by="admin-002",
        )

        assert result is not None
        assert result["id"] == "policy-minimal"
        mock_db.commit.assert_called_once()

    def test_create_governance_policy_db_error(self, mock_db):
        """Test that database errors are properly propagated."""
        mock_db.execute.side_effect = Exception("Database connection lost")

        with pytest.raises(Exception, match="Database connection lost"):
            create_governance_policy(
                db=mock_db,
                community_id="community-001",
                name="Test Policy",
                description="Test",
                rules=[],
                enforcement_level="strict",
                created_by="admin-001",
            )

        mock_db.rollback.assert_called_once()

    def test_create_governance_policy_invalid_enforcement_level(self, mock_db):
        """Test that invalid enforcement levels are rejected."""
        with pytest.raises(ValueError, match="Invalid enforcement level"):
            create_governance_policy(
                db=mock_db,
                community_id="community-001",
                name="Test Policy",
                description="Test",
                rules=[],
                enforcement_level="invalid_level",
                created_by="admin-001",
            )

    def test_create_governance_policy_empty_name(self, mock_db):
        """Test that empty policy names are rejected."""
        with pytest.raises(ValueError, match="Policy name cannot be empty"):
            create_governance_policy(
                db=mock_db,
                community_id="community-001",
                name="",
                description="Test",
                rules=[],
                enforcement_level="strict",
                created_by="admin-001",
            )

    def test_create_governance_policy_duplicate_name(self, mock_db):
        """Test handling of duplicate policy names within a community."""
        mock_db.execute.side_effect = Exception("Duplicate entry for key 'name'")

        with pytest.raises(Exception, match="Duplicate entry"):
            create_governance_policy(
                db=mock_db,
                community_id="community-001",
                name="Existing Policy",
                description="Test",
                rules=[],
                enforcement_level="strict",
                created_by="admin-001",
            )

    def test_create_governance_policy_with_complex_rules(self, mock_db):
        """Test creating a policy with complex nested rules."""
        complex_rules = [
            {
                "type": "composite",
                "logic": "AND",
                "conditions": [
                    {"type": "keyword_filter", "action": "flag", "patterns": ["bad"]},
                    {"type": "user_reputation", "action": "block", "threshold": 0.3},
                ],
            },
            {
                "type": "time_based",
                "action": "restrict",
                "schedule": {"start": "22:00", "end": "06:00", "timezone": "UTC"},
            },
        ]
        mock_db.fetchone.return_value = {"id": "policy-complex"}

        result = create_governance_policy(
            db=mock_db,
            community_id="community-001",
            name="Complex Policy",
            description="Policy with complex rules",
            rules=complex_rules,
            enforcement_level="strict",
            created_by="admin-001",
        )

        assert result is not None
        assert result["id"] == "policy-complex"
        mock_db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: get_governance_policies
# ---------------------------------------------------------------------------

class TestGetGovernancePolicies:
    """Tests for the get_governance_policies function."""

    def test_get_governance_policies_success(self, mock_db, sample_policy_record):
        """Test successful retrieval of governance policies."""
        mock_db.fetchall.return_value = [sample_policy_record]

        result = get_governance_policies(
            db=mock_db,
            community_id="community-001",
        )

        assert result is not None
        assert len(result) == 1
        assert result[0]["id"] == "policy-001"
        assert result[0]["name"] == "Content Moderation Policy"
        assert result[0]["community_id"] == "community-001"
        mock_db.execute.assert_called_once()

    def test_get_governance_policies_multiple_policies(self, mock_db):
        """Test retrieval of multiple policies for a community."""
        policies = [
            {
                "id": f"policy-{i:03d}",
                "community_id": "community-001",
                "name": f"Policy {i}",
                "description": f"Description {i}",
                "rules_json": "[]",
                "enforcement_level": "strict",
                "created_by": "admin-001",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            }
            for i in range(5)
        ]
        mock_db.fetchall.return_value = policies

        result = get_governance_policies(
            db=mock_db,
            community_id="community-001",
        )

        assert len(result) == 5
        assert all(p["community_id"] == "community-001" for p in result)

    def test_get_governance_policies_empty_result(self, mock_db):
        """Test retrieval when no policies exist for a community."""
        mock_db.fetchall.return_value = []

        result = get_governance_policies(
            db=mock_db,
            community_id="community-empty",
        )

        assert result == []
        assert isinstance(result, list)

    def test_get_governance_policies_filter_by_active(self, mock_db, sample_policy_record):
        """Test filtering policies by active status."""
        mock_db.fetchall.return_value = [sample_policy_record]

        result = get_governance_policies(
            db=mock_db,
            community_id="community-001",
            active_only=True,
        )

        assert len(result) == 1
        assert result[0]["is_active"] is True

    def test_get_governance_policies_filter_by_enforcement_level(self, mock_db):
        """Test filtering policies by enforcement level."""
        policies = [
            {
                "id": "policy-strict",
                "community_id": "community-001",
                "name": "Strict Policy",
                "description": "Strict enforcement",
                "rules_json": "[]",
                "enforcement_level": "strict",
                "created_by": "admin-001",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": "policy-lenient",
                "community_id": "community-001",
                "name": "Lenient Policy",
                "description": "Lenient enforcement",
                "rules_json": "[]",
                "enforcement_level": "lenient",
                "created_by": "admin-001",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            },
        ]
        mock_db.fetchall.return_value = [policies[0]]

        result = get_governance_policies(
            db=mock_db,
            community_id="community-001",
            enforcement_level="strict",
        )

        assert len(result) == 1
        assert result[0]["enforcement_level"] == "strict"

    def test_get_governance_policies_db_error(self, mock_db):
        """Test that database errors are properly propagated."""
        mock_db.execute.side_effect = Exception("Query timeout")

        with pytest.raises(Exception, match="Query timeout"):
            get_governance_policies(
                db=mock_db,
                community_id="community-001",
            )

    def test_get_governance_policies_with_pagination(self, mock_db):
        """Test retrieval with pagination parameters."""
        mock_db.fetchall.return_value = []

        result = get_governance_policies(
            db=mock_db,
            community_id="community-001",
            limit=10,
            offset=20,
        )

        assert result == []
        mock_db.execute.assert_called_once()

    def test_get_governance_policies_ordered_by_created_at(self, mock_db):
        """Test that policies are ordered by creation date."""
        policies = [
            {
                "id": "policy-old",
                "community_id": "community-001",
                "name": "Old Policy",
                "description": "Old",
                "rules_json": "[]",
                "enforcement_level": "strict",
                "created_by": "admin-001",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "policy-new",
                "community_id": "community-001",
                "name": "New Policy",
                "description": "New",
                "rules_json": "[]",
                "enforcement_level": "strict",
                "created_by": "admin-001",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            },
        ]
        mock_db.fetchall.return_value = policies

        result = get_governance_policies(
            db=mock_db,
            community_id="community-001",
            order_by="created_at",
            order_direction="DESC",
        )

        assert len(result) == 2
        assert result[0]["id"] == "policy-new"
        assert result[1]["id"] == "policy-old"


# ---------------------------------------------------------------------------
# Tests: enforce_governance_policy
# ---------------------------------------------------------------------------

class TestEnforceGovernancePolicy:
    """Tests for the enforce_governance_policy function."""

    def test_enforce_governance_policy_allow(self, mock_db, sample_policy_record, sample_enforcement_context):
        """Test that a compliant action is allowed."""
        mock_db.fetchone.return_value = sample_policy_record

        result = enforce_governance_policy(
            db=mock_db,
            policy_id="policy-001",
            context=sample_enforcement_context,
        )

        assert result is not None
        assert result["action"] == "allow"
        assert result["policy_id"] == "policy-001"
        assert result["reason"] is None

    def test_enforce_governance_policy_block(self, mock_db, sample_policy_record, sample_enforcement_context):
        """Test that a violating action is blocked."""
        sample_enforcement_context["content"] = "This is spam content"
        mock_db.fetchone.return_value = sample_policy_record

        result = enforce_governance_policy(
            db=mock_db,
            policy_id="policy-001",
            context=sample_enforcement_context,
        )

        assert result is not None
        assert result["action"] == "block"
        assert result["policy_id"] == "policy-001"
        assert result["reason"] is not None
        assert "spam" in result["reason"].lower() or "keyword" in result["reason"].lower()

    def test_enforce_governance_policy_throttle(self, mock_db, sample_enforcement_context):
        """Test that rate-limited actions are throttled."""
        throttle_policy = {
            "id": "policy-throttle",
            "community_id": "community-001",
            "name": "Rate Limit Policy",
            "description": "Rate limiting",
            "rules_json": '[{"type": "rate_limit", "action": "throttle", "max_posts_per_hour": 5}]',
            "enforcement_level": "strict",
            "created_by": "admin-001",
            "is_active": True,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
        }
        mock_db.fetchone.return_value = throttle_policy

        result = enforce_governance_policy(
            db=mock_db,
            policy_id="policy-throttle",
            context=sample_enforcement_context,
        )

        assert result is not None
        assert result["action"] in ("throttle", "allow")

    def test_enforce_governance_policy_flag_for_review(self, mock_db, sample_enforcement_context):
        """Test that suspicious actions are flagged for review."""
        flag_policy = {
            "id": "policy-flag",
            "community_id": "community-001",
            "name": "Flag Policy",
            "description": "Flag for review",
            "rules_json": '[{"type": "keyword_filter", "action": "flag", "patterns": ["suspicious"]}]',
            "enforcement_level": "moderate",
            "created_by": "admin-001",
            "is_active": True,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
        }
        sample_enforcement_context["content"] = "This looks suspicious"
        mock_db.fetchone.return_value = flag_policy

        result = enforce_governance_policy(
            db=mock_db,
            policy_id="policy-flag",
            context=sample_enforcement_context,
        )

        assert result is not None
        assert result["action"] == "flag"
        assert result["policy_id"] == "policy-flag"

    def test_enforce_governance_policy_inactive_policy(self, mock_db, sample_enforcement_context):
        """Test that inactive policies do not block actions."""
        inactive_policy = {
            "id": "policy-inactive",
            "community_id": "community-001",
            "name": "Inactive Policy",
            "description": "Inactive",
            "rules_json": '[{"type": "keyword_filter", "action": "block", "patterns": ["spam"]}]',
            "enforcement_level": "strict",
            "created_by": "admin-001",
            "is_active": False,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
        }
        sample_enforcement_context["content"] = "This is spam"
        mock_db.fetchone.return_value = inactive_policy

        result = enforce_governance_policy(
            db=mock_db,
            policy_id="policy-inactive",
            context=sample_enforcement_context,
        )

        assert result is not None
        assert result["action"] == "allow"

    def test_enforce_governance_policy_nonexistent_policy(self, mock_db, sample_enforcement_context):
        """Test enforcement with a non-existent policy ID."""
        mock_db.fetchone.return_value = None

        result = enforce_governance_policy(
            db=mock_db,
            policy_id="policy-nonexistent",
            context=sample_enforcement_context,
        )

        assert result is not None
        assert result["action"] == "allow"
        assert result["reason"] == "Policy not found"

    def test_enforce_governance_policy_db_error(self, mock_db, sample_enforcement_context):
        """Test that database errors during enforcement are handled."""
        mock_db.fetchone.side_effect = Exception("Database unavailable")

        with pytest.raises(Exception, match="Database unavailable"):
            enforce_governance_policy(
                db=mock_db,
                policy_id="policy-001",
                context=sample_enforcement_context,
            )

    def test_enforce_governance_policy_missing_context_fields(self, mock_db, sample_policy_record):
        """Test enforcement with missing context fields."""
        mock_db.fetchone.return_value = sample_policy_record
        incomplete_context = {"user_id": "user-123"}

        result = enforce_governance_policy(
            db=mock_db,
            policy_id="policy-001",
            context=incomplete_context,
        )

        assert result is not None
        assert result["action"] in ("allow", "flag")

    def test_enforce_governance_policy_multiple_rules(self, mock_db, sample_enforcement_context):
        """Test enforcement with a policy containing multiple rules."""
        multi_rule_policy = {
            "id": "policy-multi",
            "community_id": "community-001",
            "name": "Multi-Rule Policy",
            "description": "Multiple rules",
            "rules_json": (
                '[{"type": "keyword_filter", "action": "block", "patterns": ["spam"]},'
                '{"type": "rate_limit", "action": "throttle", "max_posts_per_hour": 10}]'
            ),
            "enforcement_level": "strict",
            "created_by": "admin-001",
            "is_active": True,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
        }
        sample_enforcement_context["content"] = "Buy cheap spam now"
        mock_db.fetchone.return_value = multi_rule_policy

        result = enforce_governance_policy(
            db=mock_db,
            policy_id="policy-multi",
            context=sample_enforcement_context,
        )

        assert result is not None
        assert result["action"] == "block"

    def test_enforce_governance_policy_community_mismatch(self, mock_db, sample_policy_record, sample_enforcement_context):
        """Test enforcement when context community doesn't match policy community."""
        sample_enforcement_context["community_id"] = "community-different"
        mock_db.fetchone.return_value = sample_policy_record

        result = enforce_governance_policy(
            db=mock_db,
            policy_id="policy-001",
            context=sample_enforcement_context,
        )

        assert result is not None
        assert result["action"] == "allow"
        assert "community" in (result.get("reason") or "").lower() or result.get("reason") is None

    def test_enforce_governance_policy_audit_log_created(self, mock_db, sample_policy_record, sample_enforcement_context):
        """Test that an audit log entry is created during enforcement."""
        mock_db.fetchone.return_value = sample_policy_record

        enforce_governance_policy(
            db=mock_db,
            policy_id="policy-001",
            context=sample_enforcement_context,
        )

        # Verify that an insert was made for the audit log
        execute_calls = mock_db.execute.call_args_list
        assert len(execute_calls) >= 1
