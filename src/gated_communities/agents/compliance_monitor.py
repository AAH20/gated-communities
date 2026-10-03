"""Compliance Monitor Agent for Gated Communities.

Monitors community compliance against governance policies, regulatory
requirements, and internal standards. Provides status checks and detailed
compliance reports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------


class ComplianceStatus(str, Enum):
    """Overall compliance status for a community."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    AT_RISK = "at_risk"
    PENDING_REVIEW = "pending_review"


class PolicyCategory(str, Enum):
    """Categories of compliance policies."""

    DATA_PRIVACY = "data_privacy"
    ACCESS_CONTROL = "access_control"
    CONTENT_MODERATION = "content_moderation"
    AUDIT_TRAIL = "audit_trail"
    MEMBER_VERIFICATION = "member_verification"
    RETENTION = "retention"


class PolicySeverity(str, Enum):
    """Severity levels for policy violations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PolicyViolation:
    """Represents a single policy violation."""

    policy_id: str
    category: PolicyCategory
    severity: PolicySeverity
    description: str
    detected_at: datetime
    resolved_at: datetime | None = None
    remediation: str | None = None

    @property
    def is_resolved(self) -> bool:
        return self.resolved_at is not None


@dataclass
class ComplianceCheckResult:
    """Result of a compliance check for a community."""

    community_id: str
    community_name: str
    status: ComplianceStatus
    checked_at: datetime
    score: float  # 0.0 – 100.0
    total_policies: int
    passed_policies: int
    failed_policies: int
    violations: list[PolicyViolation] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ComplianceReport:
    """Detailed compliance report for a community."""

    report_id: str
    community_id: str
    community_name: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    overall_status: ComplianceStatus
    overall_score: float
    summary: str
    category_breakdown: dict[str, dict[str, Any]]
    violations: list[PolicyViolation]
    recommendations: list[str]
    next_review_date: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Mock Data Store
# ---------------------------------------------------------------------------

_MOCK_COMMUNITIES: dict[str, dict[str, Any]] = {
    "comm_001": {
        "name": "Engineering Guild",
        "member_count": 342,
        "created_at": datetime(2024, 3, 15, tzinfo=UTC),
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
        "created_at": datetime(2025, 1, 10, tzinfo=UTC),
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
                detected_at=datetime(2026, 9, 28, 14, 30, tzinfo=UTC),
                remediation="Review and deactivate inactive admin accounts",
            ),
            PolicyViolation(
                policy_id="POL-AT-003",
                category=PolicyCategory.AUDIT_TRAIL,
                severity=PolicySeverity.MEDIUM,
                description="Audit log retention period below 90-day minimum",
                detected_at=datetime(2026, 9, 28, 14, 30, tzinfo=UTC),
                remediation="Extend audit log retention to meet 90-day policy",
            ),
        ],
    },
    "comm_003": {
        "name": "Design Circle",
        "member_count": 156,
        "created_at": datetime(2024, 8, 22, tzinfo=UTC),
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
                detected_at=datetime(2026, 9, 30, 9, 0, tzinfo=UTC),
                remediation="Enable AES-256 encryption for all PII data stores",
            ),
            PolicyViolation(
                policy_id="POL-CM-001",
                category=PolicyCategory.CONTENT_MODERATION,
                severity=PolicySeverity.HIGH,
                description="Content moderation queue backlog exceeds 48 hours",
                detected_at=datetime(2026, 9, 30, 9, 0, tzinfo=UTC),
                remediation="Increase moderation staff or implement automated triage",
            ),
            PolicyViolation(
                policy_id="POL-RT-001",
                category=PolicyCategory.RETENTION,
                severity=PolicySeverity.MEDIUM,
                description="Data retention schedule not enforced for deleted content",
                detected_at=datetime(2026, 9, 30, 9, 0, tzinfo=UTC),
                remediation="Implement automated retention policy enforcement",
            ),
        ],
    },
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _get_community_mock(community_id: str) -> dict[str, Any]:
    """Retrieve mock community data, generating defaults for unknown IDs."""
    if community_id in _MOCK_COMMUNITIES:
        return _MOCK_COMMUNITIES[community_id]
    # Generate deterministic mock data for unknown community IDs
    return {
        "name": f"Community {community_id}",
        "member_count": 50,
        "created_at": datetime(2025, 6, 1, tzinfo=UTC),
        "policies": {cat: {"passed": True, "last_audit": "2026-09-15"} for cat in PolicyCategory},
        "violations": [],
    }


def _calculate_score(passed: int, total: int) -> float:
    """Calculate compliance score as a percentage."""
    if total == 0:
        return 100.0
    return round((passed / total) * 100, 1)


def _determine_status(score: float, violations: list[PolicyViolation]) -> ComplianceStatus:
    """Determine overall compliance status from score and violations."""
    has_critical = any(
        v.severity == PolicySeverity.CRITICAL and not v.is_resolved for v in violations
    )
    has_high = any(v.severity == PolicySeverity.HIGH and not v.is_resolved for v in violations)

    if has_critical or score < 50:
        return ComplianceStatus.NON_COMPLIANT
    if has_high or score < 75:
        return ComplianceStatus.AT_RISK
    if score < 90:
        return ComplianceStatus.PENDING_REVIEW
    return ComplianceStatus.COMPLIANT


def _generate_recommendations(violations: list[PolicyViolation]) -> list[str]:
    """Generate remediation recommendations from violations."""
    recommendations: list[str] = []
    for v in violations:
        if not v.is_resolved and v.remediation:
            recommendations.append(f"[{v.severity.value.upper()}] {v.remediation}")
    if not recommendations:
        recommendations.append("No immediate action required. Continue regular monitoring.")
    return recommendations


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_compliance(community_id: str) -> ComplianceCheckResult:
    """Check compliance status for a given community.

    Args:
        community_id: Unique identifier of the community to check.

    Returns:
        ComplianceCheckResult with status, score, and any violations.

    Raises:
        ValueError: If community_id is empty or None.
    """
    if not community_id:
        raise ValueError("community_id must be a non-empty string")

    community = _get_community_mock(community_id)
    policies: dict[PolicyCategory, dict[str, Any]] = community["policies"]
    violations: list[PolicyViolation] = community.get("violations", [])

    total = len(policies)
    passed = sum(1 for p in policies.values() if p["passed"])
    failed = total - passed
    score = _calculate_score(passed, total)
    status = _determine_status(score, violations)
    recommendations = _generate_recommendations(violations)

    return ComplianceCheckResult(
        community_id=community_id,
        community_name=community["name"],
        status=status,
        checked_at=datetime.now(UTC),
        score=score,
        total_policies=total,
        passed_policies=passed,
        failed_policies=failed,
        violations=violations,
        recommendations=recommendations,
    )


def generate_compliance_report(community_id: str) -> ComplianceReport:
    """Generate a detailed compliance report for a given community.

    Args:
        community_id: Unique identifier of the community.

    Returns:
        ComplianceReport with full breakdown, violations, and recommendations.

    Raises:
        ValueError: If community_id is empty or None.
    """
    if not community_id:
        raise ValueError("community_id must be a non-empty string")

    check_result = check_compliance(community_id)
    community = _get_community_mock(community_id)
    now = datetime.now(UTC)
    period_start = now - timedelta(days=30)

    # Build category breakdown
    category_breakdown: dict[str, dict[str, Any]] = {}
    policies: dict[PolicyCategory, dict[str, Any]] = community["policies"]
    for cat, info in policies.items():
        cat_violations = [v for v in check_result.violations if v.category == cat]
        category_breakdown[cat.value] = {
            "status": "pass" if info["passed"] else "fail",
            "last_audit": info["last_audit"],
            "violation_count": len(cat_violations),
            "violations": [
                {
                    "policy_id": v.policy_id,
                    "severity": v.severity.value,
                    "description": v.description,
                    "detected_at": v.detected_at.isoformat(),
                    "resolved": v.is_resolved,
                }
                for v in cat_violations
            ],
        }

    # Build summary text
    if check_result.status == ComplianceStatus.COMPLIANT:
        summary = (
            f"Community '{check_result.community_name}' is fully compliant "
            f"with a score of {check_result.score}% across {check_result.total_policies} policies."
        )
    elif check_result.status == ComplianceStatus.AT_RISK:
        summary = (
            f"Community '{check_result.community_name}' is at risk with a score of "
            f"{check_result.score}%. {check_result.failed_policies} policy(s) require attention."
        )
    elif check_result.status == ComplianceStatus.NON_COMPLIANT:
        summary = (
            f"Community '{check_result.community_name}' is non-compliant with a score of "
            f"{check_result.score}%. Immediate remediation required for "
            f"{check_result.failed_policies} policy violation(s)."
        )
    else:
        summary = (
            f"Community '{check_result.community_name}' is pending review with a score of "
            f"{check_result.score}%."
        )

    return ComplianceReport(
        report_id=str(uuid.uuid4()),
        community_id=community_id,
        community_name=check_result.community_name,
        generated_at=now,
        period_start=period_start,
        period_end=now,
        overall_status=check_result.status,
        overall_score=check_result.score,
        summary=summary,
        category_breakdown=category_breakdown,
        violations=check_result.violations,
        recommendations=check_result.recommendations,
        next_review_date=now + timedelta(days=30),
        metadata={
            "member_count": community["member_count"],
            "community_created_at": community["created_at"].isoformat(),
            "report_version": "1.0",
        },
    )


# ---------------------------------------------------------------------------
# Monitoring & Flagging API
# ---------------------------------------------------------------------------


def monitor_compliance(community_id: str) -> dict[str, Any]:
    """Monitor compliance for a given community.

    Performs a full compliance check and returns a summary dictionary
    suitable for monitoring dashboards and alerting systems.

    Args:
        community_id: The unique identifier of the community to monitor.

    Returns:
        A dictionary containing compliance monitoring results with keys:
            - community_id: The community identifier.
            - community_name: Human-readable community name.
            - status: Overall compliance status ('compliant', 'non_compliant',
              'at_risk', 'pending_review').
            - score: Compliance score from 0.0 to 100.0.
            - total_policies: Total number of policies evaluated.
            - passed_policies: Number of policies that passed.
            - failed_policies: Number of policies that failed.
            - violations: List of active (unresolved) policy violations.
            - recommendations: List of remediation recommendations.
            - checked_at: ISO 8601 timestamp of when the check was performed.

    Raises:
        ValueError: If community_id is empty or None.
    """
    if not community_id:
        raise ValueError("community_id must be a non-empty string")

    result = check_compliance(community_id)

    return {
        "community_id": result.community_id,
        "community_name": result.community_name,
        "status": result.status.value,
        "score": result.score,
        "total_policies": result.total_policies,
        "passed_policies": result.passed_policies,
        "failed_policies": result.failed_policies,
        "violations": [
            {
                "policy_id": v.policy_id,
                "category": v.category.value,
                "severity": v.severity.value,
                "description": v.description,
                "detected_at": v.detected_at.isoformat(),
                "resolved": v.is_resolved,
            }
            for v in result.violations
            if not v.is_resolved
        ],
        "recommendations": result.recommendations,
        "checked_at": result.checked_at.isoformat(),
    }


def get_compliance_status(community_id: str) -> dict[str, Any]:
    """Get the current compliance status for a given community.

    Returns a lightweight status summary without full violation details,
    suitable for quick status checks and health endpoints.

    Args:
        community_id: The unique identifier of the community.

    Returns:
        A dictionary containing the compliance status with keys:
            - community_id: The community identifier.
            - community_name: Human-readable community name.
            - status: Current compliance status ('compliant', 'non_compliant',
              'at_risk', 'pending_review').
            - score: Compliance score from 0.0 to 100.0.
            - issue_count: Number of active (unresolved) policy violations.
            - last_updated: ISO 8601 timestamp of the last status update.

    Raises:
        ValueError: If community_id is empty or None.
    """
    if not community_id:
        raise ValueError("community_id must be a non-empty string")

    result = check_compliance(community_id)
    active_violations = [v for v in result.violations if not v.is_resolved]

    return {
        "community_id": result.community_id,
        "community_name": result.community_name,
        "status": result.status.value,
        "score": result.score,
        "issue_count": len(active_violations),
        "last_updated": result.checked_at.isoformat(),
    }


def flag_compliance_issue(community_id: str, issue: str) -> bool:
    """Flag a compliance issue for a given community.

    Records a new compliance issue against the specified community by
    adding a PolicyViolation entry to the community's violation list.
    The issue is associated with the CONTENT_MODERATION category and
    MEDIUM severity by default.

    Args:
        community_id: The unique identifier of the community.
        issue: Description of the compliance issue to flag.

    Returns:
        True if the issue was successfully flagged, False otherwise.

    Raises:
        ValueError: If community_id or issue is empty or None.
    """
    if not community_id:
        raise ValueError("community_id must be a non-empty string")
    if not issue:
        raise ValueError("issue must be a non-empty string")

    community = _get_community_mock(community_id)

    violation = PolicyViolation(
        policy_id=f"FLAGGED-{uuid.uuid4().hex[:8].upper()}",
        category=PolicyCategory.CONTENT_MODERATION,
        severity=PolicySeverity.MEDIUM,
        description=issue,
        detected_at=datetime.now(UTC),
        remediation="Review and address the flagged compliance issue.",
    )

    if "violations" not in community:
        community["violations"] = []
    community["violations"].append(violation)

    return True
