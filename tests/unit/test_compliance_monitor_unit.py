"""Unit tests for the compliance monitor module."""

from unittest.mock import MagicMock

import pytest

from gated_communities.compliance_monitor import (
    ComplianceMonitor,
    ComplianceReport,
    ComplianceStatus,
)


@pytest.fixture
def monitor():
    """Return a ComplianceMonitor instance with a mock community service."""
    return ComplianceMonitor(service=MagicMock())


class TestComplianceStatusEnum:
    """Tests for the ComplianceStatus enumeration."""

    def test_values(self):
        """The enum exposes the documented status values."""
        assert ComplianceStatus.COMPLIANT == "compliant"
        assert ComplianceStatus.NON_COMPLIANT == "non_compliant"
        assert ComplianceStatus.PENDING == "pending"

    def test_is_string_enum(self):
        """ComplianceStatus members compare equal to their string values."""
        assert isinstance(ComplianceStatus.COMPLIANT, str)

    def test_members_are_distinct(self):
        """Every member has a unique value."""
        values = {s.value for s in ComplianceStatus}
        assert len(values) == len(list(ComplianceStatus))


class TestComplianceReport:
    """Tests for the ComplianceReport container."""

    def test_defaults(self):
        """A report with no arguments uses pending/empty defaults."""
        report = ComplianceReport()
        assert report.id == ""
        assert report.status == ComplianceStatus.PENDING
        assert report.findings == []

    def test_custom_values(self):
        """Constructor keyword arguments populate the report."""
        report = ComplianceReport(
            id="c1",
            status=ComplianceStatus.NON_COMPLIANT,
            findings=[{"id": "v1"}],
        )
        assert report.id == "c1"
        assert report.status == ComplianceStatus.NON_COMPLIANT
        assert report.findings == [{"id": "v1"}]

    def test_findings_default_is_not_shared(self):
        """Each report gets its own findings list."""
        first = ComplianceReport()
        second = ComplianceReport()
        first.findings.append("x")
        assert second.findings == []


class TestComplianceMonitorInit:
    """Tests for ComplianceMonitor construction."""

    def test_stores_service(self):
        """The provided service is stored on the monitor."""
        service = MagicMock()
        assert ComplianceMonitor(service=service).service is service

    def test_default_service_is_none(self):
        """The service defaults to None when omitted."""
        assert ComplianceMonitor().service is None


class TestCheckCompliance:
    """Tests for ComplianceMonitor.check_compliance."""

    def test_returns_report(self, monitor):
        """check_compliance returns a ComplianceReport instance."""
        report = monitor.check_compliance("comm-123")
        assert isinstance(report, ComplianceReport)

    def test_report_id_matches_community(self, monitor):
        """The report carries the requested community id."""
        assert monitor.check_compliance("comm-123").id == "comm-123"

    def test_report_status_is_compliant(self, monitor):
        """A checked community is reported as compliant by default."""
        assert monitor.check_compliance("comm-123").status == ComplianceStatus.COMPLIANT

    def test_report_has_no_findings(self, monitor):
        """No findings are attached to a freshly generated check."""
        assert monitor.check_compliance("comm-123").findings == []

    def test_distinct_community_ids(self, monitor):
        """Each call is scoped to the requested community."""
        assert monitor.check_compliance("a").id == "a"
        assert monitor.check_compliance("b").id == "b"
