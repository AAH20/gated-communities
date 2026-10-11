"""Unit tests for gated-communities moderation analytics module."""

from __future__ import annotations

import pytest

# --- Canonical-import guard -------------------------------------------------
# The package ships BOTH a ``models/`` package and a legacy flat ``models.py``,
# and ``models/member.py`` declares ``__tablename__ = "members"`` using an
# ABSOLUTE ``from gated_communities.models.base import Base``.  If
# ``gated_communities.models.member`` (or the flat ``models.py``) is ever
# imported under a *second* module name, the shared MetaData sees "members"
# twice and SQLAlchemy aborts with::
#
#   InvalidRequestError: Table 'members' is already defined for this MetaData
#   instance.
#
# Pin the canonical package path here so this unit test can never become the
# source of that duplicate registration.
import gated_communities.models as _models  # noqa: F401  (canonical path only)

assert _models.__file__.endswith("models/__init__.py"), (
    "gated_communities.models resolved to the shadowed flat models.py; "
    "duplicate MetaData tables will result"
)

from gated_communities.analytics.moderation_analytics import (
    flag_moderation_anomaly,
    get_moderation_metrics,
    get_moderation_trends,
)


@pytest.fixture
def sample_data():
    """Provide a representative analytics payload."""
    return {"community_id": "comm-123"}


class TestGetModerationMetrics:
    """Tests for the get_moderation_metrics function."""

    def test_returns_dict(self, sample_data):
        """get_moderation_metrics should return a dictionary."""
        result = get_moderation_metrics(sample_data)
        assert isinstance(result, dict)

    def test_returns_expected_keys(self, sample_data):
        """The result exposes the documented metric keys."""
        result = get_moderation_metrics(sample_data)
        assert set(result) == {"total_items", "pending", "resolved"}

    def test_values_are_integers(self, sample_data):
        """Every metric value is a non-negative integer."""
        result = get_moderation_metrics(sample_data)
        for value in result.values():
            assert isinstance(value, int)
            assert value >= 0

    def test_defaults_are_zero(self, sample_data):
        """An empty payload yields zeroed metrics."""
        assert get_moderation_metrics(sample_data) == {
            "total_items": 0,
            "pending": 0,
            "resolved": 0,
        }

    def test_is_deterministic(self, sample_data):
        """Repeated calls with the same input are stable."""
        assert get_moderation_metrics(sample_data) == get_moderation_metrics(sample_data)


class TestGetModerationTrends:
    """Tests for the get_moderation_trends function."""

    def test_returns_dict(self, sample_data):
        """get_moderation_trends should return a dictionary."""
        assert isinstance(get_moderation_trends(sample_data), dict)

    def test_default_period(self, sample_data):
        """The default period is 30d."""
        assert get_moderation_trends(sample_data)["period"] == "30d"

    def test_custom_period(self, sample_data):
        """An explicit period is echoed back."""
        assert get_moderation_trends(sample_data, period="7d")["period"] == "7d"

    def test_trends_is_empty_list(self, sample_data):
        """With no backing data, trends is an empty list."""
        assert get_moderation_trends(sample_data)["trends"] == []

    def test_returns_expected_keys(self, sample_data):
        """The result exposes the documented trend keys."""
        assert set(get_moderation_trends(sample_data)) == {"period", "trends"}


class TestFlagModerationAnomaly:
    """Tests for the flag_moderation_anomaly function."""

    def test_returns_bool(self, sample_data):
        """The function returns a boolean."""
        assert isinstance(flag_moderation_anomaly(sample_data), bool)

    def test_defaults_to_false(self, sample_data):
        """No anomaly is flagged when no signal data is available."""
        assert flag_moderation_anomaly(sample_data) is False

    def test_is_deterministic(self, sample_data):
        """Repeated calls with the same input are stable."""
        assert flag_moderation_anomaly(sample_data) is flag_moderation_anomaly(sample_data)
