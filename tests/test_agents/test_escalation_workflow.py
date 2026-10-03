"""Tests for escalation workflow agent functions."""
from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Load the actual escalation_workflow.py module directly (shadowed by the package)
_MODULE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "gated_communities"
    / "agents"
    / "escalation_workflow.py"
)

_spec = importlib.util.spec_from_file_location(
    "gated_communities.escalation_workflow_module", _MODULE_PATH
)
escalation_workflow = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = escalation_workflow
_spec.loader.exec_module(escalation_workflow)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_escalation_store():
    """Clear the in-memory escalation store before each test."""
    escalation_workflow._ESCALATIONS.clear()
    yield
    escalation_workflow._ESCALATIONS.clear()


@pytest.fixture
def sample_issue_id():
    """Return a deterministic issue ID."""
    return "issue-12345"


@pytest.fixture
def sample_escalation_id():
    """Return a deterministic escalation ID."""
    return "esc-abcde"


@pytest.fixture
def created_escalation(sample_issue_id):
    """Create an escalation and return its record."""
    return escalation_workflow.create_escalation(
        issue_id=sample_issue_id, priority="high"
    )


# ---------------------------------------------------------------------------
# Tests for create_escalation
# ---------------------------------------------------------------------------


class TestCreateEscalation:
    """Tests for the create_escalation function."""

    def test_create_escalation_success(self, sample_issue_id):
        """Test successful escalation creation returns correct fields."""
        result = escalation_workflow.create_escalation(
            issue_id=sample_issue_id, priority="high"
        )

        assert result is not None
        assert result["issue_id"] == sample_issue_id
        assert result["priority"] == "high"
        assert result["status"] == "open"
        assert "escalation_id" in result
        assert "created_at" in result
        assert result["resolved_at"] is None

    def test_create_escalation_generates_unique_ids(self, sample_issue_id):
        """Test that each escalation gets a unique escalation_id."""
        result1 = escalation_workflow.create_escalation(
            issue_id=sample_issue_id, priority="low"
        )
        result2 = escalation_workflow.create_escalation(
            issue_id=sample_issue_id, priority="medium"
        )

        assert result1["escalation_id"] != result2["escalation_id"]

    def test_create_escalation_all_valid_priorities(self, sample_issue_id):
        """Test that all valid priority levels are accepted."""
        for priority in ("low", "medium", "high", "critical"):
            result = escalation_workflow.create_escalation(
                issue_id=sample_issue_id, priority=priority
            )
            assert result["priority"] == priority

    def test_create_escalation_priority_case_insensitive(self, sample_issue_id):
        """Test that priority is case-insensitive."""
        result = escalation_workflow.create_escalation(
            issue_id=sample_issue_id, priority="HIGH"
        )
        assert result["priority"] == "high"

    def test_create_escalation_stores_in_store(self, sample_issue_id):
        """Test that created escalation is stored in the internal store."""
        result = escalation_workflow.create_escalation(
            issue_id=sample_issue_id, priority="high"
        )

        assert result["escalation_id"] in escalation_workflow._ESCALATIONS
        stored = escalation_workflow._ESCALATIONS[result["escalation_id"]]
        assert stored["issue_id"] == sample_issue_id
        assert stored["status"] == "open"

    def test_create_escalation_invalid_priority_raises(self, sample_issue_id):
        """Test that invalid priority raises ValueError."""
        with pytest.raises(ValueError, match="Invalid priority"):
            escalation_workflow.create_escalation(
                issue_id=sample_issue_id, priority="super-urgent"
            )

    def test_create_escalation_empty_issue_id_raises(self):
        """Test that empty issue_id raises ValueError."""
        with pytest.raises(ValueError, match="issue_id must not be empty"):
            escalation_workflow.create_escalation(issue_id="", priority="high")

    def test_create_escalation_whitespace_issue_id_raises(self):
        """Test that whitespace-only issue_id raises ValueError."""
        with pytest.raises(ValueError, match="issue_id must not be empty"):
            escalation_workflow.create_escalation(issue_id="   ", priority="high")

    def test_create_escalation_non_string_issue_id_raises(self):
        """Test that non-string issue_id raises TypeError."""
        with pytest.raises(TypeError, match="issue_id must be a string"):
            escalation_workflow.create_escalation(issue_id=123, priority="high")

    def test_create_escalation_non_string_priority_raises(self):
        """Test that non-string priority raises TypeError."""
        with pytest.raises(TypeError, match="priority must be a string"):
            escalation_workflow.create_escalation(
                issue_id="issue-1", priority=123
            )

    def test_create_escalation_created_at_is_isoformat(self, sample_issue_id):
        """Test that created_at is a valid ISO 8601 timestamp."""
        result = escalation_workflow.create_escalation(
            issue_id=sample_issue_id, priority="high"
        )

        # Should not raise
        datetime.fromisoformat(result["created_at"])


# ---------------------------------------------------------------------------
# Tests for get_escalation_status
# ---------------------------------------------------------------------------


class TestGetEscalationStatus:
    """Tests for the get_escalation_status function."""

    def test_get_escalation_status_open(self, created_escalation):
        """Test retrieving status of an open escalation."""
        result = escalation_workflow.get_escalation_status(
            created_escalation["escalation_id"]
        )

        assert result is not None
        assert result["escalation_id"] == created_escalation["escalation_id"]
        assert result["status"] == "open"
        assert result["issue_id"] == created_escalation["issue_id"]
        assert result["priority"] == created_escalation["priority"]

    def test_get_escalation_status_returns_copy(self, created_escalation):
        """Test that returned dict is a copy, not the stored reference."""
        result = escalation_workflow.get_escalation_status(
            created_escalation["escalation_id"]
        )

        # Mutating the returned dict should not affect the store
        result["status"] = "tampered"
        fresh = escalation_workflow.get_escalation_status(
            created_escalation["escalation_id"]
        )
        assert fresh["status"] == "open"

    def test_get_escalation_status_resolved(self, created_escalation):
        """Test retrieving status after escalation is resolved."""
        escalation_workflow.resolve_escalation(created_escalation["escalation_id"])

        result = escalation_workflow.get_escalation_status(
            created_escalation["escalation_id"]
        )

        assert result["status"] == "resolved"
        assert result["resolved_at"] is not None

    def test_get_escalation_status_not_found_raises(self):
        """Test that non-existent escalation raises KeyError."""
        with pytest.raises(KeyError, match="No escalation found"):
            escalation_workflow.get_escalation_status("nonexistent-id")

    def test_get_escalation_status_empty_id_raises(self):
        """Test that empty escalation_id raises ValueError."""
        with pytest.raises(ValueError, match="escalation_id must not be empty"):
            escalation_workflow.get_escalation_status("")

    def test_get_escalation_status_whitespace_id_raises(self):
        """Test that whitespace-only escalation_id raises ValueError."""
        with pytest.raises(ValueError, match="escalation_id must not be empty"):
            escalation_workflow.get_escalation_status("   ")

    def test_get_escalation_status_non_string_id_raises(self):
        """Test that non-string escalation_id raises TypeError."""
        with pytest.raises(TypeError, match="escalation_id must be a string"):
            escalation_workflow.get_escalation_status(123)

    def test_get_escalation_status_includes_all_fields(self, created_escalation):
        """Test that status response includes all expected fields."""
        result = escalation_workflow.get_escalation_status(
            created_escalation["escalation_id"]
        )

        expected_fields = {
            "escalation_id",
            "issue_id",
            "priority",
            "status",
            "created_at",
            "resolved_at",
        }
        assert expected_fields.issubset(result.keys())


# ---------------------------------------------------------------------------
# Tests for resolve_escalation
# ---------------------------------------------------------------------------


class TestResolveEscalation:
    """Tests for the resolve_escalation function."""

    def test_resolve_escalation_success(self, created_escalation):
        """Test successful escalation resolution returns True."""
        result = escalation_workflow.resolve_escalation(
            created_escalation["escalation_id"]
        )

        assert result is True

    def test_resolve_escalation_updates_status(self, created_escalation):
        """Test that resolving updates the stored escalation status."""
        escalation_id = created_escalation["escalation_id"]

        escalation_workflow.resolve_escalation(escalation_id)

        stored = escalation_workflow._ESCALATIONS[escalation_id]
        assert stored["status"] == "resolved"

    def test_resolve_escalation_sets_resolved_at(self, created_escalation):
        """Test that resolving sets resolved_at to a valid timestamp."""
        escalation_id = created_escalation["escalation_id"]

        before = datetime.now(timezone.utc)
        escalation_workflow.resolve_escalation(escalation_id)
        after = datetime.now(timezone.utc)

        stored = escalation_workflow._ESCALATIONS[escalation_id]
        resolved_at = datetime.fromisoformat(stored["resolved_at"])
        # resolved_at is timezone-aware; compare as UTC
        assert before <= resolved_at <= after

    def test_resolve_escalation_already_resolved_returns_false(
        self, created_escalation
    ):
        """Test that resolving an already-resolved escalation returns False."""
        escalation_id = created_escalation["escalation_id"]

        first = escalation_workflow.resolve_escalation(escalation_id)
        second = escalation_workflow.resolve_escalation(escalation_id)

        assert first is True
        assert second is False

    def test_resolve_escalation_not_found_raises(self):
        """Test that resolving non-existent escalation raises KeyError."""
        with pytest.raises(KeyError, match="No escalation found"):
            escalation_workflow.resolve_escalation("nonexistent-id")

    def test_resolve_escalation_empty_id_raises(self):
        """Test that empty escalation_id raises ValueError."""
        with pytest.raises(ValueError, match="escalation_id must not be empty"):
            escalation_workflow.resolve_escalation("")

    def test_resolve_escalation_whitespace_id_raises(self):
        """Test that whitespace-only escalation_id raises ValueError."""
        with pytest.raises(ValueError, match="escalation_id must not be empty"):
            escalation_workflow.resolve_escalation("   ")

    def test_resolve_escalation_non_string_id_raises(self):
        """Test that non-string escalation_id raises TypeError."""
        with pytest.raises(TypeError, match="escalation_id must be a string"):
            escalation_workflow.resolve_escalation(123)

    def test_resolve_escalation_does_not_change_issue_id(
        self, created_escalation, sample_issue_id
    ):
        """Test that resolving does not alter the issue_id."""
        escalation_id = created_escalation["escalation_id"]

        escalation_workflow.resolve_escalation(escalation_id)

        stored = escalation_workflow._ESCALATIONS[escalation_id]
        assert stored["issue_id"] == sample_issue_id

    def test_resolve_escalation_does_not_change_priority(
        self, created_escalation
    ):
        """Test that resolving does not alter the priority."""
        escalation_id = created_escalation["escalation_id"]
        original_priority = created_escalation["priority"]

        escalation_workflow.resolve_escalation(escalation_id)

        stored = escalation_workflow._ESCALATIONS[escalation_id]
        assert stored["priority"] == original_priority
