"""Comprehensive agent tests for the Compliance Monitor module.

Tests cover:
- monitor_compliance: full compliance monitoring with status, score, violations
- get_compliance_status: lightweight status summary for health checks
- flag_compliance_issue: recording new compliance issues against communities
"""

from __future__ import annotations

import importlib.util
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

# Load compliance_monitor module directly to avoid broken __init__ imports
_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "gated_communities"
    / "agents"
    / "compliance_monitor.py"
)
_spec = importlib.util.spec_from_file_location("compliance_monitor", _MODULE_PATH)
compliance_monitor = importlib.util.module_from_spec(_spec)
sys.modules["compliance_monitor"] = compliance_monitor
_spec.loader.exec_module(compliance_monitor)

ComplianceStatus = compliance_monitor.ComplianceStatus
PolicyCategory = compliance_monitor.PolicyCategory
PolicySeverity = compliance_monitor.PolicySeverity
PolicyViolation = compliance_monitor.PolicyViolation
check_compliance = compliance_monitor.check_compliance
flag_compliance_issue = compliance_monitor.flag_compliance_issue
get_compliance_status = compliance_monitor.get_compliance_status
monitor_compliance = compliance_monitor.monitor_compliance


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def compliant_community_id() -> str:
    """Community ID for a fully compliant community (all policies pass)."""
    return "comm_001"


@pytest.fixture
def at_risk_community_id() -> str:
    """Community ID for an at-risk community (some policies fail, has violations)."""
    return "comm_002"


@pytest.fixture
def non_compliant_community_id() -> str:
    """Community ID for a non-compliant community (critical violations)."""
    return "comm_003"


@pytest.fixture
def unknown_community_id() -> str:
    """Community ID not in mock data (generates default compliant data)."""
    return "comm_unknown_999"


@pytest.fixture
def sample_violation() -> PolicyViolation:
    """Create a sample unresolved policy violation."""
    return PolicyViolation(
        policy_id="POL-TEST-001",
        category=PolicyCategory.DATA_PRIVACY,
        severity=PolicySeverity.HIGH,
        description="Test violation for unit testing",
        detected_at=datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc),
        remediation="Fix the test violation",
    )


@pytest.fixture
def resolved_violation() -> PolicyViolation:
    """Create a sample resolved policy violation."""
    return PolicyViolation(
        policy_id="POL-TEST-002",
        category=PolicyCategory.ACCESS_CONTROL,
        severity=PolicySeverity.LOW,
        description="Resolved test violation",
        detected_at=datetime(2026, 9, 10, 10, 0, tzinfo=timezone.utc),
        resolved_at=datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc),
        remediation="Already fixed",
    )


@pytest.fixture
def mock_community_data() -> Dict[str, Any]:
    """Provide a fresh copy of mock community data for isolation."""
    return {
        "comm_001": {
            "name": "Engineering Guild",
            "member_count": 342,
            "created_at": datetime(2024, 3, 15, tzinfo=timezone.utc),
            "policies": {
                PolicyCategory.DATA_PRIVACY: {"passed": True, "last_audit": "2026-09-15"},
                PolicyCategory.ACCESS_CONTROL: {"passed": True, "last_audit": "2026-09-20"},
                PolicyCategory.CONTENT_MODERATION: {"passed": True, "last_audit": "2026-09-10"},
                PolicyCategory.AUDIT_TRAIL: {"passed": True, "last_audit": "2026-09-25"},
                PolicyCategory.MEMBER_VERIFICATION: {"passed": True, "last_audit": "2026-09-18"},
                PolicyCategory.RETENTION: {"passed": True, "last_audit": "2026-09-22"},
            },
            "violations": [],
        },
        "comm_002": {
            "name": "Product Leaders Forum",
            "member_count": 89,
            "created_at": datetime(2025, 1, 10, tzinfo=timezone.utc),
            "policies": {
                PolicyCategory.DATA_PRIVACY: {"passed": True, "last_audit": "2026-09-12"},
                PolicyCategory.ACCESS_CONTROL: {"passed": False, "last_audit": "2026-09-28"},
                PolicyCategory.CONTENT_MODERATION: {"passed": True, "last_audit": "2026-09-14"},
                PolicyCategory.AUDIT_TRAIL: {"passed": False, "last_audit": "2026-09-28"},
                PolicyCategory.MEMBER_VERIFICATION: {"passed": True, "last_audit": "2026-09-16"},
                PolicyCategory.RETENTION: {"passed": True, "last_audit": "2026-09-20"},
            },
            "violations": [
                PolicyViolation(
                    policy_id="POL-AC-001",
                    category=PolicyCategory.ACCESS_CONTROL,
                    severity=PolicySeverity.HIGH,
                    description="Inactive admin accounts not deactivated within 30 days",
                    detected_at=datetime(2026, 9, 28, 14, 30, tzinfo=timezone.utc),
                    remediation="Review and deactivate inactive admin accounts",
                ),
                PolicyViolation(
                    policy_id="POL-AT-003",
                    category=PolicyCategory.AUDIT_TRAIL,
                    severity=PolicySeverity.MEDIUM,
                    description="Audit log retention period below 90-day minimum",
                    detected_at=datetime(2026, 9, 28, 14, 30, tzinfo=timezone.utc),
                    remediation="Extend audit log retention to meet 90-day policy",
                ),
            ],
        },
        "comm_003": {
            "name": "Design Circle",
            "member_count": 156,
            "created_at": datetime(2024, 8, 22, tzinfo=timezone.utc),
            "policies": {
                PolicyCategory.DATA_PRIVACY: {"passed": False, "last_audit": "2026-09-30"},
                PolicyCategory.ACCESS_CONTROL: {"passed": True, "last_audit": "2026-09-25"},
                PolicyCategory.CONTENT_MODERATION: {"passed": False, "last_audit": "2026-09-30"},
                PolicyCategory.AUDIT_TRAIL: {"passed": True, "last_audit": "2026-09-27"},
                PolicyCategory.MEMBER_VERIFICATION: {"passed": True, "last_audit": "2026-09-19"},
                PolicyCategory.RETENTION: {"passed": False, "last_audit": "2026-09-30"},
            },
            "violations": [
                PolicyViolation(
                    policy_id="POL-DP-002",
                    category=PolicyCategory.DATA_PRIVACY,
                    severity=PolicySeverity.CRITICAL,
                    description="Member PII stored without encryption at rest",
                    detected_at=datetime(2026, 9, 30, 9, 0, tzinfo=timezone.utc),
                    remediation="Enable AES-256 encryption for all PII data stores",
                ),
                PolicyViolation(
                    policy_id="POL-CM-001",
                    category=PolicyCategory.CONTENT_MODERATION,
                    severity=PolicySeverity.HIGH,
                    description="Content moderation queue backlog exceeds 48 hours",
                    detected_at=datetime(2026, 9, 30, 9, 0, tzinfo=timezone.utc),
                    remediation="Increase moderation staff or implement automated triage",
                ),
                PolicyViolation(
                    policy_id="POL-RT-001",
                    category=PolicyCategory.RETENTION,
                    severity=PolicySeverity.MEDIUM,
                    description="Data retention schedule not enforced for deleted content",
                    detected_at=datetime(2026, 9, 30, 9, 0, tzinfo=timezone.utc),
                    remediation="Implement automated retention policy enforcement",
                ),
            ],
        },
    }


@pytest.fixture(autouse=True)
def reset_mock_data(mock_community_data):
    """Reset mock community data before each test to ensure isolation."""
    original = compliance_monitor._MOCK_COMMUNITIES.copy()
    compliance_monitor._MOCK_COMMUNITIES.clear()
    compliance_monitor._MOCK_COMMUNITIES.update(mock_community_data)
    yield
    compliance_monitor._MOCK_COMMUNITIES.clear()
    compliance_monitor._MOCK_COMMUNITIES.update(original)


# ===========================================================================
# Tests for monitor_compliance
# ===========================================================================


class TestMonitorCompliance:
    """Tests for the monitor_compliance function."""

    def test_monitor_compliance_returns_dict(self, compliant_community_id):
        """monitor_compliance should return a dictionary."""
        result = monitor_compliance(compliant_community_id)
        assert isinstance(result, dict)

    def test_monitor_compliance_required_keys(self, compliant_community_id):
        """Result must contain all required monitoring keys."""
        result = monitor_compliance(compliant_community_id)
        required_keys = {
            "community_id",
            "community_name",
            "status",
            "score",
            "total_policies",
            "passed_policies",
            "failed_policies",
            "violations",
            "recommendations",
            "checked_at",
        }
        assert required_keys.issubset(result.keys())

    def test_monitor_compliance_compliant_community(self, compliant_community_id):
        """A community with all policies passing should be COMPLIANT."""
        result = monitor_compliance(compliant_community_id)
        assert result["status"] == ComplianceStatus.COMPLIANT.value
        assert result["score"] == 100.0
        assert result["total_policies"] == 6
        assert result["passed_policies"] == 6
        assert result["failed_policies"] == 0
        assert result["violations"] == []
        assert len(result["recommendations"]) >= 1

    def test_monitor_compliance_at_risk_community(self, at_risk_community_id):
        """A community with failed policies and HIGH violations should be AT_RISK."""
        result = monitor_compliance(at_risk_community_id)
        assert result["status"] == ComplianceStatus.AT_RISK.value
        assert result["score"] < 100.0
        assert result["failed_policies"] > 0
        assert len(result["violations"]) > 0
        assert len(result["recommendations"]) > 0

    def test_monitor_compliance_non_compliant_community(self, non_compliant_community_id):
        """A community with CRITICAL violations should be NON_COMPLIANT."""
        result = monitor_compliance(non_compliant_community_id)
        assert result["status"] == ComplianceStatus.NON_COMPLIANT.value
        assert result["score"] <= 50.0
        assert result["failed_policies"] > 0
        assert len(result["violations"]) > 0

    def test_monitor_compliance_unknown_community(self, unknown_community_id):
        """Unknown community IDs should generate default compliant data."""
        result = monitor_compliance(unknown_community_id)
        assert result["community_id"] == unknown_community_id
        assert result["status"] == ComplianceStatus.COMPLIANT.value
        assert result["score"] == 100.0
        assert result["total_policies"] == 6
        assert result["passed_policies"] == 6
        assert result["failed_policies"] == 0

    def test_monitor_compliance_community_id_preserved(self, compliant_community_id):
        """The community_id in the result should match the input."""
        result = monitor_compliance(compliant_community_id)
        assert result["community_id"] == compliant_community_id

    def test_monitor_compliance_community_name_preserved(self, compliant_community_id):
        """The community_name should match the mock data."""
        result = monitor_compliance(compliant_community_id)
        assert result["community_name"] == "Engineering Guild"

    def test_monitor_compliance_checked_at_is_iso_format(self, compliant_community_id):
        """checked_at should be a valid ISO 8601 timestamp."""
        result = monitor_compliance(compliant_community_id)
        # Should not raise
        datetime.fromisoformat(result["checked_at"])

    def test_monitor_compliance_violations_only_unresolved(self, at_risk_community_id):
        """Only unresolved violations should appear in the violations list."""
        result = monitor_compliance(at_risk_community_id)
        for violation in result["violations"]:
            assert violation["resolved"] is False

    def test_monitor_compliance_violation_structure(self, at_risk_community_id):
        """Each violation dict should have the expected keys."""
        result = monitor_compliance(at_risk_community_id)
        if result["violations"]:
            violation = result["violations"][0]
            expected_keys = {
                "policy_id",
                "category",
                "severity",
                "description",
                "detected_at",
                "resolved",
            }
            assert expected_keys.issubset(violation.keys())

    def test_monitor_compliance_recommendations_for_compliant(self, compliant_community_id):
        """Compliant communities should have a 'no action' recommendation."""
        result = monitor_compliance(compliant_community_id)
        assert any("No immediate action" in r for r in result["recommendations"])

    def test_monitor_compliance_recommendations_for_violations(self, at_risk_community_id):
        """At-risk communities should have remediation recommendations."""
        result = monitor_compliance(at_risk_community_id)
        assert len(result["recommendations"]) > 0
        # Recommendations should contain severity prefixes
        assert any(r.startswith("[") for r in result["recommendations"])

    def test_monitor_compliance_empty_community_id_raises(self):
        """Empty string community_id should raise ValueError."""
        with pytest.raises(ValueError, match="community_id must be a non-empty string"):
            monitor_compliance("")

    def test_monitor_compliance_none_community_id_raises(self):
        """None community_id should raise ValueError."""
        with pytest.raises(ValueError, match="community_id must be a non-empty string"):
            monitor_compliance(None)

    def test_monitor_compliance_score_range(self, compliant_community_id):
        """Score should be between 0.0 and 100.0."""
        result = monitor_compliance(compliant_community_id)
        assert 0.0 <= result["score"] <= 100.0

    def test_monitor_compliance_score_calculation(self, at_risk_community_id):
        """Score should be calculated as (passed / total) * 100."""
        result = monitor_compliance(at_risk_community_id)
        expected_score = round(
            (result["passed_policies"] / result["total_policies"]) * 100, 1
        )
        assert result["score"] == expected_score

    def test_monitor_compliance_total_equals_passed_plus_failed(self, at_risk_community_id):
        """total_policies should equal passed_policies + failed_policies."""
        result = monitor_compliance(at_risk_community_id)
        assert result["total_policies"] == (
            result["passed_policies"] + result["failed_policies"]
        )

    def test_monitor_compliance_violations_have_valid_severity(self, non_compliant_community_id):
        """All violations should have a valid severity value."""
        result = monitor_compliance(non_compliant_community_id)
        valid_severities = {"critical", "high", "medium", "low"}
        for violation in result["violations"]:
            assert violation["severity"] in valid_severities

    def test_monitor_compliance_violations_have_valid_category(self, non_compliant_community_id):
        """All violations should have a valid category value."""
        result = monitor_compliance(non_compliant_community_id)
        valid_categories = {
            "data_privacy",
            "access_control",
            "content_moderation",
            "audit_trail",
            "member_verification",
            "retention",
        }
        for violation in result["violations"]:
            assert violation["category"] in valid_categories

    def test_monitor_compliance_detected_at_is_iso_format(self, at_risk_community_id):
        """Violation detected_at should be ISO 8601 format."""
        result = monitor_compliance(at_risk_community_id)
        for violation in result["violations"]:
            datetime.fromisoformat(violation["detected_at"])

    def test_monitor_compliance_multiple_calls_consistent(self, compliant_community_id):
        """Multiple calls with same ID should produce consistent results."""
        result1 = monitor_compliance(compliant_community_id)
        result2 = monitor_compliance(compliant_community_id)
        assert result1["status"] == result2["status"]
        assert result1["score"] == result2["score"]
        assert result1["total_policies"] == result2["total_policies"]


# ===========================================================================
# Tests for get_compliance_status
# ===========================================================================


class TestGetComplianceStatus:
    """Tests for the get_compliance_status function."""

    def test_get_compliance_status_returns_dict(self, compliant_community_id):
        """get_compliance_status should return a dictionary."""
        result = get_compliance_status(compliant_community_id)
        assert isinstance(result, dict)

    def test_get_compliance_status_required_keys(self, compliant_community_id):
        """Result must contain all required status keys."""
        result = get_compliance_status(compliant_community_id)
        required_keys = {
            "community_id",
            "community_name",
            "status",
            "score",
            "issue_count",
            "last_updated",
        }
        assert required_keys.issubset(result.keys())

    def test_get_compliance_status_compliant_community(self, compliant_community_id):
        """A compliant community should have status COMPLIANT and 0 issues."""
        result = get_compliance_status(compliant_community_id)
        assert result["status"] == ComplianceStatus.COMPLIANT.value
        assert result["score"] == 100.0
        assert result["issue_count"] == 0

    def test_get_compliance_status_at_risk_community(self, at_risk_community_id):
        """An at-risk community should have AT_RISK status and >0 issues."""
        result = get_compliance_status(at_risk_community_id)
        assert result["status"] == ComplianceStatus.AT_RISK.value
        assert result["issue_count"] > 0

    def test_get_compliance_status_non_compliant_community(self, non_compliant_community_id):
        """A non-compliant community should have NON_COMPLIANT status and >0 issues."""
        result = get_compliance_status(non_compliant_community_id)
        assert result["status"] == ComplianceStatus.NON_COMPLIANT.value
        assert result["issue_count"] > 0

    def test_get_compliance_status_unknown_community(self, unknown_community_id):
        """Unknown community should return COMPLIANT with 0 issues."""
        result = get_compliance_status(unknown_community_id)
        assert result["community_id"] == unknown_community_id
        assert result["status"] == ComplianceStatus.COMPLIANT.value
        assert result["issue_count"] == 0

    def test_get_compliance_status_community_id_preserved(self, compliant_community_id):
        """The community_id in the result should match the input."""
        result = get_compliance_status(compliant_community_id)
        assert result["community_id"] == compliant_community_id

    def test_get_compliance_status_community_name_preserved(self, compliant_community_id):
        """The community_name should match the mock data."""
        result = get_compliance_status(compliant_community_id)
        assert result["community_name"] == "Engineering Guild"

    def test_get_compliance_status_last_updated_is_iso_format(self, compliant_community_id):
        """last_updated should be a valid ISO 8601 timestamp."""
        result = get_compliance_status(compliant_community_id)
        datetime.fromisoformat(result["last_updated"])

    def test_get_compliance_status_issue_count_matches_violations(self, at_risk_community_id):
        """issue_count should equal the number of unresolved violations."""
        result = get_compliance_status(at_risk_community_id)
        # comm_002 has 2 unresolved violations
        assert result["issue_count"] == 2

    def test_get_compliance_status_empty_community_id_raises(self):
        """Empty string community_id should raise ValueError."""
        with pytest.raises(ValueError, match="community_id must be a non-empty string"):
            get_compliance_status("")

    def test_get_compliance_status_none_community_id_raises(self):
        """None community_id should raise ValueError."""
        with pytest.raises(ValueError, match="community_id must be a non-empty string"):
            get_compliance_status(None)

    def test_get_compliance_status_score_range(self, compliant_community_id):
        """Score should be between 0.0 and 100.0."""
        result = get_compliance_status(compliant_community_id)
        assert 0.0 <= result["score"] <= 100.0

    def test_get_compliance_status_issue_count_is_int(self, compliant_community_id):
        """issue_count should be an integer."""
        result = get_compliance_status(compliant_community_id)
        assert isinstance(result["issue_count"], int)

    def test_get_compliance_status_issue_count_non_negative(self, compliant_community_id):
        """issue_count should never be negative."""
        result = get_compliance_status(compliant_community_id)
        assert result["issue_count"] >= 0

    def test_get_compliance_status_does_not_include_violations_list(self, at_risk_community_id):
        """get_compliance_status should NOT include a full violations list (lightweight)."""
        result = get_compliance_status(at_risk_community_id)
        assert "violations" not in result

    def test_get_compliance_status_does_not_include_recommendations(self, at_risk_community_id):
        """get_compliance_status should NOT include recommendations (lightweight)."""
        result = get_compliance_status(at_risk_community_id)
        assert "recommendations" not in result

    def test_get_compliance_status_does_not_include_total_policies(self, compliant_community_id):
        """get_compliance_status should NOT include total_policies (lightweight)."""
        result = get_compliance_status(compliant_community_id)
        assert "total_policies" not in result

    def test_get_compliance_status_does_not_include_passed_policies(self, compliant_community_id):
        """get_compliance_status should NOT include passed_policies (lightweight)."""
        result = get_compliance_status(compliant_community_id)
        assert "passed_policies" not in result

    def test_get_compliance_status_does_not_include_failed_policies(self, compliant_community_id):
        """get_compliance_status should NOT include failed_policies (lightweight)."""
        result = get_compliance_status(compliant_community_id)
        assert "failed_policies" not in result

    def test_get_compliance_status_multiple_calls_consistent(self, compliant_community_id):
        """Multiple calls with same ID should produce consistent results."""
        result1 = get_compliance_status(compliant_community_id)
        result2 = get_compliance_status(compliant_community_id)
        assert result1["status"] == result2["status"]
        assert result1["score"] == result2["score"]
        assert result1["issue_count"] == result2["issue_count"]


# ===========================================================================
# Tests for flag_compliance_issue
# ===========================================================================


class TestFlagComplianceIssue:
    """Tests for the flag_compliance_issue function."""

    def test_flag_compliance_issue_returns_true(self, compliant_community_id):
        """flag_compliance_issue should return True on success."""
        result = flag_compliance_issue(compliant_community_id, "Test issue description")
        assert result is True

    def test_flag_compliance_issue_adds_violation(self, compliant_community_id):
        """Flagging an issue should add a violation to the community."""
        community_before = compliance_monitor._get_community_mock(compliant_community_id)
        violations_before = len(community_before.get("violations", []))

        flag_compliance_issue(compliant_community_id, "New test issue")

        community_after = compliance_monitor._get_community_mock(compliant_community_id)
        violations_after = len(community_after.get("violations", []))

        assert violations_after == violations_before + 1

    def test_flag_compliance_issue_violation_has_correct_category(self, compliant_community_id):
        """Flagged issues should be categorized as CONTENT_MODERATION."""

        flag_compliance_issue(compliant_community_id, "Test issue")

        community = compliance_monitor._get_community_mock(compliant_community_id)
        new_violation = community["violations"][-1]
        assert new_violation.category == PolicyCategory.CONTENT_MODERATION

    def test_flag_compliance_issue_violation_has_correct_severity(self, compliant_community_id):
        """Flagged issues should have MEDIUM severity."""

        flag_compliance_issue(compliant_community_id, "Test issue")

        community = compliance_monitor._get_community_mock(compliant_community_id)
        new_violation = community["violations"][-1]
        assert new_violation.severity == PolicySeverity.MEDIUM

    def test_flag_compliance_issue_violation_has_description(self, compliant_community_id):
        """Flagged issue should store the provided description."""

        flag_compliance_issue(compliant_community_id, "Specific test issue description")

        community = compliance_monitor._get_community_mock(compliant_community_id)
        new_violation = community["violations"][-1]
        assert new_violation.description == "Specific test issue description"

    def test_flag_compliance_issue_violation_has_remediation(self, compliant_community_id):
        """Flagged issue should have a default remediation message."""

        flag_compliance_issue(compliant_community_id, "Test issue")

        community = compliance_monitor._get_community_mock(compliant_community_id)
        new_violation = community["violations"][-1]
        assert new_violation.remediation is not None
        assert "Review and address" in new_violation.remediation

    def test_flag_compliance_issue_violation_has_policy_id(self, compliant_community_id):
        """Flagged issue should have a FLAGGED- prefixed policy_id."""

        flag_compliance_issue(compliant_community_id, "Test issue")

        community = compliance_monitor._get_community_mock(compliant_community_id)
        new_violation = community["violations"][-1]
        assert new_violation.policy_id.startswith("FLAGGED-")

    def test_flag_compliance_issue_violation_has_detected_at(self, compliant_community_id):
        """Flagged issue should have a detected_at timestamp."""

        flag_compliance_issue(compliant_community_id, "Test issue")

        community = compliance_monitor._get_community_mock(compliant_community_id)
        new_violation = community["violations"][-1]
        assert new_violation.detected_at is not None
        assert isinstance(new_violation.detected_at, datetime)

    def test_flag_compliance_issue_violation_is_unresolved(self, compliant_community_id):
        """Newly flagged issues should be unresolved."""

        flag_compliance_issue(compliant_community_id, "Test issue")

        community = compliance_monitor._get_community_mock(compliant_community_id)
        new_violation = community["violations"][-1]
        assert new_violation.resolved_at is None
        assert not new_violation.is_resolved

    def test_flag_compliance_issue_empty_community_id_raises(self):
        """Empty string community_id should raise ValueError."""
        with pytest.raises(ValueError, match="community_id must be a non-empty string"):
            flag_compliance_issue("", "Test issue")

    def test_flag_compliance_issue_none_community_id_raises(self):
        """None community_id should raise ValueError."""
        with pytest.raises(ValueError, match="community_id must be a non-empty string"):
            flag_compliance_issue(None, "Test issue")

    def test_flag_compliance_issue_empty_issue_raises(self, compliant_community_id):
        """Empty string issue should raise ValueError."""
        with pytest.raises(ValueError, match="issue must be a non-empty string"):
            flag_compliance_issue(compliant_community_id, "")

    def test_flag_compliance_issue_none_issue_raises(self, compliant_community_id):
        """None issue should raise ValueError."""
        with pytest.raises(ValueError, match="issue must be a non-empty string"):
            flag_compliance_issue(compliant_community_id, None)

    def test_flag_compliance_issue_both_empty_raises(self):
        """Both empty should raise ValueError (community_id checked first)."""
        with pytest.raises(ValueError, match="community_id must be a non-empty string"):
            flag_compliance_issue("", "")

    def test_flag_compliance_issue_unknown_community(self, unknown_community_id):
        """Flagging an issue for unknown community should still work."""
        result = flag_compliance_issue(unknown_community_id, "Test issue for unknown")
        assert result is True

    def test_flag_compliance_issue_unknown_community_creates_violations_list(self, unknown_community_id):
        """Flagging for unknown community should succeed (violations list is generated on access)."""
        result = flag_compliance_issue(unknown_community_id, "Test issue")
        assert result is True
        # Unknown communities generate fresh mock data each access, so violations
        # are not persisted across calls. The function still succeeds.
        community = compliance_monitor._get_community_mock(unknown_community_id)
        assert "violations" in community

    def test_flag_compliance_issue_multiple_flags(self, compliant_community_id):
        """Multiple flags should each add a separate violation."""

        flag_compliance_issue(compliant_community_id, "First issue")
        flag_compliance_issue(compliant_community_id, "Second issue")
        flag_compliance_issue(compliant_community_id, "Third issue")

        community = compliance_monitor._get_community_mock(compliant_community_id)
        assert len(community["violations"]) == 3

    def test_flag_compliance_issue_unique_policy_ids(self, compliant_community_id):
        """Each flagged issue should have a unique policy_id."""

        flag_compliance_issue(compliant_community_id, "First issue")
        flag_compliance_issue(compliant_community_id, "Second issue")

        community = compliance_monitor._get_community_mock(compliant_community_id)
        policy_ids = [v.policy_id for v in community["violations"]]
        assert len(policy_ids) == len(set(policy_ids))

    def test_flag_compliance_issue_affects_compliance_status(self, compliant_community_id):
        """Flagging an issue should change the compliance status."""
        # Before flagging: compliant
        status_before = get_compliance_status(compliant_community_id)
        assert status_before["issue_count"] == 0

        # Flag an issue
        flag_compliance_issue(compliant_community_id, "New compliance issue")

        # After flagging: should have 1 issue
        status_after = get_compliance_status(compliant_community_id)
        assert status_after["issue_count"] == 1

    def test_flag_compliance_issue_affects_monitor_compliance(self, compliant_community_id):
        """Flagging an issue should be reflected in monitor_compliance output."""
        # Before flagging
        monitor_before = monitor_compliance(compliant_community_id)
        violations_before = len(monitor_before["violations"])

        # Flag an issue
        flag_compliance_issue(compliant_community_id, "New monitored issue")

        # After flagging
        monitor_after = monitor_compliance(compliant_community_id)
        violations_after = len(monitor_after["violations"])

        assert violations_after == violations_before + 1

    def test_flag_compliance_issue_with_special_characters(self, compliant_community_id):
        """Issue descriptions with special characters should be handled."""
        special_issue = "Issue with special chars: <script>alert('xss')</script> & \"quotes\""
        result = flag_compliance_issue(compliant_community_id, special_issue)
        assert result is True


        community = compliance_monitor._get_community_mock(compliant_community_id)
        assert community["violations"][-1].description == special_issue

    def test_flag_compliance_issue_with_long_description(self, compliant_community_id):
        """Very long issue descriptions should be handled."""
        long_issue = "A" * 10000
        result = flag_compliance_issue(compliant_community_id, long_issue)
        assert result is True


        community = compliance_monitor._get_community_mock(compliant_community_id)
        assert community["violations"][-1].description == long_issue

    def test_flag_compliance_issue_with_unicode(self, compliant_community_id):
        """Unicode issue descriptions should be handled."""
        unicode_issue = "Unicode test: 你好世界 🌍 émojis"
        result = flag_compliance_issue(compliant_community_id, unicode_issue)
        assert result is True


        community = compliance_monitor._get_community_mock(compliant_community_id)
        assert community["violations"][-1].description == unicode_issue