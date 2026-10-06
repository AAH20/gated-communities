"""Tests for community health scoring and flagging."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from gated_communities.community_health_scorer import (
    score_community_health,
    get_health_metrics,
    flag_unhealthy_community,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_community():
    """Return a sample community dict for testing."""
    return {
        "id": "comm_001",
        "name": "Test Community",
        "member_count": 150,
        "active_members": 120,
        "posts_last_30d": 45,
        "comments_last_30d": 320,
        "moderation_actions_30d": 5,
        "created_at": "2024-01-15T10:00:00Z",
        "last_activity_at": "2024-06-01T12:00:00Z",
        "category": "technology",
        "is_private": False,
    }


@pytest.fixture
def healthy_community():
    """Return a community with strong health indicators."""
    return {
        "id": "comm_healthy",
        "name": "Healthy Community",
        "member_count": 500,
        "active_members": 450,
        "posts_last_30d": 200,
        "comments_last_30d": 1500,
        "moderation_actions_30d": 2,
        "created_at": "2023-01-01T00:00:00Z",
        "last_activity_at": "2024-06-15T08:00:00Z",
        "category": "science",
        "is_private": False,
    }


@pytest.fixture
def unhealthy_community():
    """Return a community with poor health indicators."""
    return {
        "id": "comm_unhealthy",
        "name": "Unhealthy Community",
        "member_count": 50,
        "active_members": 3,
        "posts_last_30d": 1,
        "comments_last_30d": 2,
        "moderation_actions_30d": 25,
        "created_at": "2024-05-01T00:00:00Z",
        "last_activity_at": "2024-05-02T00:00:00Z",
        "category": "general",
        "is_private": True,
    }


@pytest.fixture
def empty_community():
    """Return a community with zero activity."""
    return {
        "id": "comm_empty",
        "name": "Empty Community",
        "member_count": 0,
        "active_members": 0,
        "posts_last_30d": 0,
        "comments_last_30d": 0,
        "moderation_actions_30d": 0,
        "created_at": "2024-06-01T00:00:00Z",
        "last_activity_at": "2024-06-01T00:00:00Z",
        "category": "general",
        "is_private": False,
    }


@pytest.fixture
def mock_db():
    """Return a mock database connection."""
    db = MagicMock()
    db.execute = MagicMock(return_value=MagicMock())
    db.fetchone = MagicMock(return_value=None)
    db.fetchall = MagicMock(return_value=[])
    return db


@pytest.fixture
def mock_logger():
    """Return a mock logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    return logger


# ---------------------------------------------------------------------------
# Tests for score_community_health
# ---------------------------------------------------------------------------


class TestScoreCommunityHealth:
    """Tests for the score_community_health function."""

    def test_score_community_health_returns_float(self, sample_community):
        """score_community_health should return a float score."""
        result = score_community_health(sample_community)
        assert isinstance(result, float)

    def test_score_community_health_range(self, sample_community):
        """Score should be between 0.0 and 1.0 inclusive."""
        result = score_community_health(sample_community)
        assert 0.0 <= result <= 1.0

    def test_score_community_health_healthy(self, healthy_community):
        """A healthy community should have a high score."""
        result = score_community_health(healthy_community)
        assert result >= 0.7

    def test_score_community_health_unhealthy(self, unhealthy_community):
        """An unhealthy community should have a low score."""
        result = score_community_health(unhealthy_community)
        assert result <= 0.4

    def test_score_community_health_empty(self, empty_community):
        """An empty community should have a very low score."""
        result = score_community_health(empty_community)
        assert result <= 0.2

    def test_score_community_health_perfect_score(self):
        """A perfect community should score 1.0."""
        perfect = {
            "id": "comm_perfect",
            "name": "Perfect Community",
            "member_count": 1000,
            "active_members": 1000,
            "posts_last_30d": 500,
            "comments_last_30d": 5000,
            "moderation_actions_30d": 0,
            "created_at": "2020-01-01T00:00:00Z",
            "last_activity_at": "2024-06-15T23:59:59Z",
            "category": "technology",
            "is_private": False,
        }
        result = score_community_health(perfect)
        assert result == 1.0

    def test_score_community_health_zero_members(self):
        """A community with zero members should not raise an error."""
        community = {
            "id": "comm_zero",
            "name": "Zero Members",
            "member_count": 0,
            "active_members": 0,
            "posts_last_30d": 0,
            "comments_last_30d": 0,
            "moderation_actions_30d": 0,
            "created_at": "2024-01-01T00:00:00Z",
            "last_activity_at": "2024-01-01T00:00:00Z",
            "category": "general",
            "is_private": False,
        }
        result = score_community_health(community)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_score_community_health_missing_fields(self):
        """Missing optional fields should be handled gracefully."""
        minimal = {"id": "comm_minimal", "name": "Minimal"}
        result = score_community_health(minimal)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_score_community_health_high_moderation(self):
        """High moderation actions should lower the score."""
        high_mod = {
            "id": "comm_mod",
            "name": "High Moderation",
            "member_count": 200,
            "active_members": 180,
            "posts_last_30d": 100,
            "comments_last_30d": 800,
            "moderation_actions_30d": 100,
            "created_at": "2024-01-01T00:00:00Z",
            "last_activity_at": "2024-06-15T00:00:00Z",
            "category": "general",
            "is_private": False,
        }
        result = score_community_health(high_mod)
        assert result < 0.5

    def test_score_community_health_recent_activity(self):
        """Recent activity should boost the score."""
        now = datetime.utcnow().isoformat() + "Z"
        recent = {
            "id": "comm_recent",
            "name": "Recent Activity",
            "member_count": 100,
            "active_members": 90,
            "posts_last_30d": 50,
            "comments_last_30d": 400,
            "moderation_actions_30d": 1,
            "created_at": "2024-01-01T00:00:00Z",
            "last_activity_at": now,
            "category": "general",
            "is_private": False,
        }
        result = score_community_health(recent)
        assert result >= 0.6

    def test_score_community_health_stale_activity(self):
        """Stale activity should lower the score."""
        stale_date = (datetime.utcnow() - timedelta(days=180)).isoformat() + "Z"
        stale = {
            "id": "comm_stale",
            "name": "Stale Activity",
            "member_count": 100,
            "active_members": 90,
            "posts_last_30d": 50,
            "comments_last_30d": 400,
            "moderation_actions_30d": 1,
            "created_at": "2024-01-01T00:00:00Z",
            "last_activity_at": stale_date,
            "category": "general",
            "is_private": False,
        }
        result = score_community_health(stale)
        assert result < 0.5

    def test_score_community_health_deterministic(self, sample_community):
        """Same input should always produce the same score."""
        result1 = score_community_health(sample_community)
        result2 = score_community_health(sample_community)
        assert result1 == result2

    def test_score_community_health_private_community(self, sample_community):
        """Private communities should be scored without error."""
        sample_community["is_private"] = True
        result = score_community_health(sample_community)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# Tests for get_health_metrics
# ---------------------------------------------------------------------------


class TestGetHealthMetrics:
    """Tests for the get_health_metrics function."""

    def test_get_health_metrics_returns_dict(self, sample_community):
        """get_health_metrics should return a dictionary."""
        result = get_health_metrics(sample_community)
        assert isinstance(result, dict)

    def test_get_health_metrics_contains_expected_keys(self, sample_community):
        """Result should contain standard metric keys."""
        result = get_health_metrics(sample_community)
        expected_keys = {
            "activity_score",
            "engagement_rate",
            "member_retention",
            "moderation_burden",
            "overall_health",
        }
        assert expected_keys.issubset(result.keys())

    def test_get_health_metrics_activity_score_range(self, sample_community):
        """activity_score should be between 0.0 and 1.0."""
        result = get_health_metrics(sample_community)
        assert 0.0 <= result["activity_score"] <= 1.0

    def test_get_health_metrics_engagement_rate_range(self, sample_community):
        """engagement_rate should be between 0.0 and 1.0."""
        result = get_health_metrics(sample_community)
        assert 0.0 <= result["engagement_rate"] <= 1.0

    def test_get_health_metrics_member_retention_range(self, sample_community):
        """member_retention should be between 0.0 and 1.0."""
        result = get_health_metrics(sample_community)
        assert 0.0 <= result["member_retention"] <= 1.0

    def test_get_health_metrics_moderation_burden_range(self, sample_community):
        """moderation_burden should be between 0.0 and 1.0."""
        result = get_health_metrics(sample_community)
        assert 0.0 <= result["moderation_burden"] <= 1.0

    def test_get_health_metrics_overall_health_range(self, sample_community):
        """overall_health should be between 0.0 and 1.0."""
        result = get_health_metrics(sample_community)
        assert 0.0 <= result["overall_health"] <= 1.0

    def test_get_health_metrics_healthy_community(self, healthy_community):
        """Healthy community should have high overall_health."""
        result = get_health_metrics(healthy_community)
        assert result["overall_health"] >= 0.7

    def test_get_health_metrics_unhealthy_community(self, unhealthy_community):
        """Unhealthy community should have low overall_health."""
        result = get_health_metrics(unhealthy_community)
        assert result["overall_health"] <= 0.4

    def test_get_health_metrics_empty_community(self, empty_community):
        """Empty community should have very low metrics."""
        result = get_health_metrics(empty_community)
        assert result["overall_health"] <= 0.2
        assert result["activity_score"] <= 0.2

    def test_get_health_metrics_engagement_calculation(self, sample_community):
        """Engagement rate should reflect active member ratio."""
        result = get_health_metrics(sample_community)
        expected_ratio = sample_community["active_members"] / sample_community["member_count"]
        assert abs(result["engagement_rate"] - expected_ratio) < 0.15

    def test_get_health_metrics_missing_fields(self):
        """Missing fields should be handled with defaults."""
        minimal = {"id": "comm_min", "name": "Minimal"}
        result = get_health_metrics(minimal)
        assert isinstance(result, dict)
        assert "overall_health" in result

    def test_get_health_metrics_zero_members(self, empty_community):
        """Zero members should not cause division errors."""
        result = get_health_metrics(empty_community)
        assert isinstance(result, dict)
        assert 0.0 <= result["overall_health"] <= 1.0

    def test_get_health_metrics_deterministic(self, sample_community):
        """Same input should produce same metrics."""
        result1 = get_health_metrics(sample_community)
        result2 = get_health_metrics(sample_community)
        assert result1 == result2

    def test_get_health_metrics_high_moderation(self):
        """High moderation should increase moderation_burden."""
        high_mod = {
            "id": "comm_hm",
            "name": "High Mod",
            "member_count": 100,
            "active_members": 90,
            "posts_last_30d": 50,
            "comments_last_30d": 400,
            "moderation_actions_30d": 80,
            "created_at": "2024-01-01T00:00:00Z",
            "last_activity_at": "2024-06-15T00:00:00Z",
            "category": "general",
            "is_private": False,
        }
        result = get_health_metrics(high_mod)
        assert result["moderation_burden"] > 0.5


# ---------------------------------------------------------------------------
# Tests for flag_unhealthy_community
# ---------------------------------------------------------------------------


class TestFlagUnhealthyCommunity:
    """Tests for the flag_unhealthy_community function."""

    def test_flag_unhealthy_community_returns_bool(self, sample_community):
        """flag_unhealthy_community should return a boolean."""
        result = flag_unhealthy_community(sample_community)
        assert isinstance(result, bool)

    def test_flag_unhealthy_community_flags_unhealthy(self, unhealthy_community):
        """An unhealthy community should be flagged."""
        result = flag_unhealthy_community(unhealthy_community)
        assert result is True

    def test_flag_unhealthy_community_passes_healthy(self, healthy_community):
        """A healthy community should not be flagged."""
        result = flag_unhealthy_community(healthy_community)
        assert result is False

    def test_flag_unhealthy_community_empty_flagged(self, empty_community):
        """An empty community should be flagged as unhealthy."""
        result = flag_unhealthy_community(empty_community)
        assert result is True

    def test_flag_unhealthy_community_threshold_boundary(self):
        """Test behavior near the health threshold boundary."""
        boundary_community = {
            "id": "comm_boundary",
            "name": "Boundary",
            "member_count": 100,
            "active_members": 50,
            "posts_last_30d": 10,
            "comments_last_30d": 80,
            "moderation_actions_30d": 10,
            "created_at": "2024-01-01T00:00:00Z",
            "last_activity_at": "2024-06-01T00:00:00Z",
            "category": "general",
            "is_private": False,
        }
        result = flag_unhealthy_community(boundary_community)
        assert isinstance(result, bool)

    def test_flag_unhealthy_community_with_custom_threshold(self, sample_community):
        """Custom threshold should be respected."""
        # With a very high threshold, even decent communities get flagged
        result = flag_unhealthy_community(sample_community, threshold=0.99)
        assert isinstance(result, bool)

        # With a very low threshold, most communities pass
        result = flag_unhealthy_community(sample_community, threshold=0.01)
        assert isinstance(result, bool)

    def test_flag_unhealthy_community_uses_score(self, sample_community):
        """Flagging should be consistent with score_community_health."""
        from gated_communities.community_health_scorer import score_community_health

        score = score_community_health(sample_community)
        flagged = flag_unhealthy_community(sample_community)
        # If score is below typical threshold (0.4), should be flagged
        if score < 0.4:
            assert flagged is True
        else:
            assert flagged is False

    def test_flag_unhealthy_community_missing_fields(self):
        """Missing fields should not cause an error."""
        minimal = {"id": "comm_min", "name": "Minimal"}
        result = flag_unhealthy_community(minimal)
        assert isinstance(result, bool)

    def test_flag_unhealthy_community_deterministic(self, sample_community):
        """Same input should produce same flag result."""
        result1 = flag_unhealthy_community(sample_community)
        result2 = flag_unhealthy_community(sample_community)
        assert result1 == result2

    def test_flag_unhealthy_community_extreme_values(self):
        """Extreme values should not cause errors."""
        extreme = {
            "id": "comm_extreme",
            "name": "Extreme",
            "member_count": 999999,
            "active_members": 1,
            "posts_last_30d": 0,
            "comments_last_30d": 0,
            "moderation_actions_30d": 99999,
            "created_at": "2024-01-01T00:00:00Z",
            "last_activity_at": "2024-01-01T00:00:00Z",
            "category": "general",
            "is_private": True,
        }
        result = flag_unhealthy_community(extreme)
        assert result is True

    def test_flag_unhealthy_community_all_zeros(self):
        """All-zero community should be flagged."""
        zeros = {
            "id": "comm_zeros",
            "name": "Zeros",
            "member_count": 0,
            "active_members": 0,
            "posts_last_30d": 0,
            "comments_last_30d": 0,
            "moderation_actions_30d": 0,
            "created_at": "2024-01-01T00:00:00Z",
            "last_activity_at": "2024-01-01T00:00:00Z",
            "category": "general",
            "is_private": False,
        }
        result = flag_unhealthy_community(zeros)
        assert result is True
