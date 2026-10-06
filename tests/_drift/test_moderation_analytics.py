"""
Comprehensive agent tests for moderation analytics functions.

Tests cover:
- get_moderation_metrics: retrieval of moderation KPIs
- get_moderation_trends: time-series trend analysis
- flag_moderation_anomaly: anomaly detection and flagging
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call
from typing import Any

from gated_communities.moderation_analytics import (
    get_moderation_metrics,
    get_moderation_trends,
    flag_moderation_anomaly,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_moderation_data():
    """Sample raw moderation data for testing."""
    return {
        "total_flags": 150,
        "resolved_flags": 120,
        "pending_flags": 30,
        "false_positives": 15,
        "true_positives": 105,
        "avg_resolution_time_hours": 4.5,
        "moderators_active": 8,
        "communities_covered": 25,
        "period_start": "2024-01-01T00:00:00Z",
        "period_end": "2024-01-31T23:59:59Z",
    }


@pytest.fixture
def sample_trend_data():
    """Sample time-series trend data for testing."""
    base_date = datetime(2024, 1, 1)
    return [
        {
            "date": (base_date + timedelta(days=i)).isoformat() + "Z",
            "flags_raised": 10 + i * 2,
            "flags_resolved": 8 + i,
            "resolution_rate": 0.75 + i * 0.01,
            "avg_resolution_hours": 5.0 - i * 0.1,
        }
        for i in range(30)
    ]


@pytest.fixture
def sample_anomaly_data():
    """Sample data containing anomalies for testing."""
    return {
        "current_period": {
            "flags_raised": 500,
            "flags_resolved": 450,
            "resolution_rate": 0.90,
            "avg_resolution_hours": 2.0,
        },
        "historical_baseline": {
            "flags_raised": 100,
            "flags_resolved": 90,
            "resolution_rate": 0.90,
            "avg_resolution_hours": 4.0,
        },
        "thresholds": {
            "flags_raised_zscore": 3.0,
            "resolution_rate_deviation": 0.15,
            "resolution_time_multiplier": 2.0,
        },
    }


@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn


@pytest.fixture
def mock_metrics_response():
    """Mock response from metrics API."""
    return {
        "status": "success",
        "data": {
            "total_moderation_actions": 1250,
            "actions_by_type": {
                "content_removal": 400,
                "user_warning": 350,
                "user_ban": 200,
                "appeal_approved": 150,
                "appeal_denied": 150,
            },
            "actions_by_moderator": {
                "mod_1": 300,
                "mod_2": 280,
                "mod_3": 250,
                "mod_4": 220,
                "mod_5": 200,
            },
            "community_health_scores": {
                "community_a": 0.92,
                "community_b": 0.85,
                "community_c": 0.78,
            },
        },
        "metadata": {
            "generated_at": "2024-01-31T23:59:59Z",
            "period": "2024-01",
        },
    }


@pytest.fixture
def mock_trends_response():
    """Mock response from trends API."""
    return {
        "status": "success",
        "data": {
            "daily": [
                {"date": f"2024-01-{i+1:02d}", "count": 20 + i}
                for i in range(31)
            ],
            "weekly": [
                {"week": f"2024-W{i+1}", "count": 140 + i * 5}
                for i in range(5)
            ],
            "monthly": [
                {"month": f"2024-{i+1:02d}", "count": 600 + i * 20}
                for i in range(12)
            ],
            "aggregates": {
                "mean_daily": 35.5,
                "median_daily": 34.0,
                "std_dev_daily": 8.2,
                "trend_direction": "increasing",
                "trend_slope": 0.45,
            },
        },
    }


@pytest.fixture
def mock_anomaly_response():
    """Mock response from anomaly detection."""
    return {
        "status": "success",
        "data": {
            "anomalies_detected": 3,
            "anomalies": [
                {
                    "id": "anomaly_1",
                    "type": "spike_in_flags",
                    "severity": "high",
                    "community": "community_x",
                    "timestamp": "2024-01-15T14:30:00Z",
                    "expected_value": 50,
                    "actual_value": 250,
                    "deviation_factor": 5.0,
                },
                {
                    "id": "anomaly_2",
                    "type": "resolution_rate_drop",
                    "severity": "medium",
                    "community": "community_y",
                    "timestamp": "2024-01-20T09:00:00Z",
                    "expected_value": 0.90,
                    "actual_value": 0.65,
                    "deviation_factor": 0.28,
                },
                {
                    "id": "anomaly_3",
                    "type": "resolution_time_surge",
                    "severity": "low",
                    "community": "community_z",
                    "timestamp": "2024-01-25T18:00:00Z",
                    "expected_value": 4.0,
                    "actual_value": 12.5,
                    "deviation_factor": 3.125,
                },
            ],
        },
    }


# ---------------------------------------------------------------------------
# Tests for get_moderation_metrics
# ---------------------------------------------------------------------------


class TestGetModerationMetrics:
    """Test suite for get_moderation_metrics function."""

    def test_get_moderation_metrics_returns_dict(self, mock_metrics_response):
        """Test that get_moderation_metrics returns a dictionary."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_metrics_from_db",
            return_value=mock_metrics_response,
        ):
            result = get_moderation_metrics(period="2024-01")
            assert isinstance(result, dict)

    def test_get_moderation_metrics_contains_required_keys(
        self, mock_metrics_response
    ):
        """Test that result contains all required metric keys."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_metrics_from_db",
            return_value=mock_metrics_response,
        ):
            result = get_moderation_metrics(period="2024-01")
            assert "total_moderation_actions" in result
            assert "actions_by_type" in result
            assert "actions_by_moderator" in result
            assert "community_health_scores" in result

    def test_get_moderation_metrics_total_actions_correct(
        self, mock_metrics_response
    ):
        """Test that total moderation actions is correctly returned."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_metrics_from_db",
            return_value=mock_metrics_response,
        ):
            result = get_moderation_metrics(period="2024-01")
            assert result["total_moderation_actions"] == 1250

    def test_get_moderation_metrics_actions_by_type(
        self, mock_metrics_response
    ):
        """Test that actions_by_type breakdown is correct."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_metrics_from_db",
            return_value=mock_metrics_response,
        ):
            result = get_moderation_metrics(period="2024-01")
            actions = result["actions_by_type"]
            assert actions["content_removal"] == 400
            assert actions["user_warning"] == 350
            assert actions["user_ban"] == 200
            assert actions["appeal_approved"] == 150
            assert actions["appeal_denied"] == 150

    def test_get_moderation_metrics_actions_sum_matches_total(
        self, mock_metrics_response
    ):
        """Test that sum of action types equals total actions."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_metrics_from_db",
            return_value=mock_metrics_response,
        ):
            result = get_moderation_metrics(period="2024-01")
            action_sum = sum(result["actions_by_type"].values())
            assert action_sum == result["total_moderation_actions"]

    def test_get_moderation_metrics_community_health_scores(
        self, mock_metrics_response
    ):
        """Test that community health scores are correctly returned."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_metrics_from_db",
            return_value=mock_metrics_response,
        ):
            result = get_moderation_metrics(period="2024-01")
            scores = result["community_health_scores"]
            assert scores["community_a"] == 0.92
            assert scores["community_b"] == 0.85
            assert scores["community_c"] == 0.78

    def test_get_moderation_metrics_with_community_filter(
        self, mock_metrics_response
    ):
        """Test filtering metrics by specific community."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_metrics_from_db",
            return_value=mock_metrics_response,
        ) as mock_fetch:
            result = get_moderation_metrics(
                period="2024-01", community_id="community_a"
            )
            mock_fetch.assert_called_once()
            call_kwargs = mock_fetch.call_args
            assert "community_a" in str(call_kwargs)

    def test_get_moderation_metrics_with_date_range(
        self, mock_metrics_response
    ):
        """Test metrics retrieval with custom date range."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_metrics_from_db",
            return_value=mock_metrics_response,
        ) as mock_fetch:
            result = get_moderation_metrics(
                start_date="2024-01-01", end_date="2024-01-31"
            )
            assert result is not None
            mock_fetch.assert_called_once()

    def test_get_moderation_metrics_empty_data(self):
        """Test handling of empty data response."""
        empty_response = {
            "status": "success",
            "data": {
                "total_moderation_actions": 0,
                "actions_by_type": {},
                "actions_by_moderator": {},
                "community_health_scores": {},
            },
        }
        with patch(
            "src.gated_communities.moderation_analytics._fetch_metrics_from_db",
            return_value=empty_response,
        ):
            result = get_moderation_metrics(period="2024-02")
            assert result["total_moderation_actions"] == 0
            assert result["actions_by_type"] == {}

    def test_get_moderation_metrics_invalid_period_raises_error(self):
        """Test that invalid period format raises ValueError."""
        with pytest.raises(ValueError):
            get_moderation_metrics(period="invalid-period")

    def test_get_moderation_metrics_db_error_raises_exception(self):
        """Test that database errors are properly propagated."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_metrics_from_db",
            side_effect=ConnectionError("Database connection failed"),
        ):
            with pytest.raises(ConnectionError):
                get_moderation_metrics(period="2024-01")

    def test_get_moderation_metrics_caching(self, mock_metrics_response):
        """Test that repeated calls use cached data when appropriate."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_metrics_from_db",
            return_value=mock_metrics_response,
        ) as mock_fetch:
            result1 = get_moderation_metrics(period="2024-01", use_cache=True)
            result2 = get_moderation_metrics(period="2024-01", use_cache=True)
            assert result1 == result2

    def test_get_moderation_metrics_moderator_breakdown(
        self, mock_metrics_response
    ):
        """Test that moderator breakdown is correctly structured."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_metrics_from_db",
            return_value=mock_metrics_response,
        ):
            result = get_moderation_metrics(period="2024-01")
            moderators = result["actions_by_moderator"]
            assert len(moderators) == 5
            assert all(
                isinstance(v, int) for v in moderators.values()
            )

    def test_get_moderation_metrics_health_score_range(
        self, mock_metrics_response
    ):
        """Test that health scores are within valid range [0, 1]."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_metrics_from_db",
            return_value=mock_metrics_response,
        ):
            result = get_moderation_metrics(period="2024-01")
            for score in result["community_health_scores"].values():
                assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Tests for get_moderation_trends
# ---------------------------------------------------------------------------


class TestGetModerationTrends:
    """Test suite for get_moderation_trends function."""

    def test_get_moderation_trends_returns_dict(self, mock_trends_response):
        """Test that get_moderation_trends returns a dictionary."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=mock_trends_response,
        ):
            result = get_moderation_trends(period="2024-01")
            assert isinstance(result, dict)

    def test_get_moderation_trends_contains_time_series(
        self, mock_trends_response
    ):
        """Test that result contains daily, weekly, and monthly series."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=mock_trends_response,
        ):
            result = get_moderation_trends(period="2024-01")
            assert "daily" in result
            assert "weekly" in result
            assert "monthly" in result

    def test_get_moderation_trends_daily_series_length(
        self, mock_trends_response
    ):
        """Test that daily series has correct number of data points."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=mock_trends_response,
        ):
            result = get_moderation_trends(period="2024-01")
            assert len(result["daily"]) == 31

    def test_get_moderation_trends_aggregates_present(
        self, mock_trends_response
    ):
        """Test that aggregate statistics are included."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=mock_trends_response,
        ):
            result = get_moderation_trends(period="2024-01")
            assert "aggregates" in result
            agg = result["aggregates"]
            assert "mean_daily" in agg
            assert "median_daily" in agg
            assert "std_dev_daily" in agg
            assert "trend_direction" in agg
            assert "trend_slope" in agg

    def test_get_moderation_trends_trend_direction(
        self, mock_trends_response
    ):
        """Test that trend direction is correctly identified."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=mock_trends_response,
        ):
            result = get_moderation_trends(period="2024-01")
            assert result["aggregates"]["trend_direction"] == "increasing"

    def test_get_moderation_trends_trend_slope_positive(
        self, mock_trends_response
    ):
        """Test that positive trend slope indicates increasing trend."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=mock_trends_response,
        ):
            result = get_moderation_trends(period="2024-01")
            assert result["aggregates"]["trend_slope"] > 0

    def test_get_moderation_trends_with_granularity_daily(
        self, mock_trends_response
    ):
        """Test trends retrieval with daily granularity."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=mock_trends_response,
        ) as mock_fetch:
            result = get_moderation_trends(
                period="2024-01", granularity="daily"
            )
            assert "daily" in result
            mock_fetch.assert_called_once()

    def test_get_moderation_trends_with_granularity_weekly(
        self, mock_trends_response
    ):
        """Test trends retrieval with weekly granularity."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=mock_trends_response,
        ):
            result = get_moderation_trends(
                period="2024-01", granularity="weekly"
            )
            assert "weekly" in result

    def test_get_moderation_trends_with_granularity_monthly(
        self, mock_trends_response
    ):
        """Test trends retrieval with monthly granularity."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=mock_trends_response,
        ):
            result = get_moderation_trends(
                period="2024-01", granularity="monthly"
            )
            assert "monthly" in result

    def test_get_moderation_trends_with_community_filter(
        self, mock_trends_response
    ):
        """Test trends retrieval filtered by community."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=mock_trends_response,
        ) as mock_fetch:
            result = get_moderation_trends(
                period="2024-01", community_id="community_a"
            )
            assert result is not None
            mock_fetch.assert_called_once()

    def test_get_moderation_trends_empty_data(self):
        """Test handling of empty trends data."""
        empty_response = {
            "status": "success",
            "data": {
                "daily": [],
                "weekly": [],
                "monthly": [],
                "aggregates": {},
            },
        }
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=empty_response,
        ):
            result = get_moderation_trends(period="2024-02")
            assert result["daily"] == []
            assert result["weekly"] == []

    def test_get_moderation_trends_invalid_granularity_raises_error(self):
        """Test that invalid granularity raises ValueError."""
        with pytest.raises(ValueError):
            get_moderation_trends(period="2024-01", granularity="yearly")

    def test_get_moderation_trends_data_point_structure(
        self, mock_trends_response
    ):
        """Test that each data point has required fields."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=mock_trends_response,
        ):
            result = get_moderation_trends(period="2024-01")
            for point in result["daily"]:
                assert "date" in point
                assert "count" in point

    def test_get_moderation_trends_mean_calculation(
        self, mock_trends_response
    ):
        """Test that mean daily value is correctly calculated."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=mock_trends_response,
        ):
            result = get_moderation_trends(period="2024-01")
            daily_counts = [p["count"] for p in result["daily"]]
            expected_mean = sum(daily_counts) / len(daily_counts)
            assert (
                abs(result["aggregates"]["mean_daily"] - expected_mean) < 0.01
            )

    def test_get_moderation_trends_db_error_raises_exception(self):
        """Test that database errors are properly propagated."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            side_effect=ConnectionError("Database connection failed"),
        ):
            with pytest.raises(ConnectionError):
                get_moderation_trends(period="2024-01")

    def test_get_moderation_trends_weekly_aggregation(
        self, mock_trends_response
    ):
        """Test that weekly data is properly aggregated."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=mock_trends_response,
        ):
            result = get_moderation_trends(period="2024-01")
            assert len(result["weekly"]) == 5
            for point in result["weekly"]:
                assert "week" in point
                assert "count" in point

    def test_get_moderation_trends_monthly_aggregation(
        self, mock_trends_response
    ):
        """Test that monthly data is properly aggregated."""
        with patch(
            "src.gated_communities.moderation_analytics._fetch_trends_from_db",
            return_value=mock_trends_response,
        ):
            result = get_moderation_trends(period="2024-01")
            assert len(result["monthly"]) == 12
            for point in result["monthly"]:
                assert "month" in point
                assert "count" in point


# ---------------------------------------------------------------------------
# Tests for flag_moderation_anomaly
# ---------------------------------------------------------------------------


class TestFlagModerationAnomaly:
    """Test suite for flag_moderation_anomaly function."""

    def test_flag_moderation_anomaly_returns_dict(self, mock_anomaly_response):
        """Test that flag_moderation_anomaly returns a dictionary."""
        with patch(
            "src.gated_communities.moderation_analytics._detect_anomalies",
            return_value=mock_anomaly_response,
        ):
            result = flag_moderation_anomaly(
                community_id="community_x", period="2024-01"
            )
            assert isinstance(result, dict)

    def test_flag_moderation_anomaly_detects_anomalies(
        self, mock_anomaly_response
    ):
        """Test that anomalies are correctly detected."""
        with patch(
            "src.gated_communities.moderation_analytics._detect_anomalies",
            return_value=mock_anomaly_response,
        ):
            result = flag_moderation_anomaly(
                community_id="community_x", period="2024-01"
            )
            assert result["anomalies_detected"] == 3
            assert len(result["anomalies"]) == 3

    def test_flag_moderation_anomaly_anomaly_structure(
        self, mock_anomaly_response
    ):
        """Test that each anomaly has required fields."""
        with patch(
            "src.gated_communities.moderation_analytics._detect_anomalies",
            return_value=mock_anomaly_response,
        ):
            result = flag_moderation_anomaly(
                community_id="community_x", period="2024-01"
            )
            for anomaly in result["anomalies"]:
                assert "id" in anomaly
                assert "type" in anomaly
                assert "severity" in anomaly
                assert "community" in anomaly
                assert "timestamp" in anomaly
                assert "expected_value" in anomaly
                assert "actual_value" in anomaly
                assert "deviation_factor" in anomaly

    def test_flag_moderation_anomaly_severity_levels(
        self, mock_anomaly_response
    ):
        """Test that severity levels are valid."""
        valid_severities = {"low", "medium", "high", "critical"}
        with patch(
            "src.gated_communities.moderation_analytics._detect_anomalies",
            return_value=mock_anomaly_response,
        ):
            result = flag_moderation_anomaly(
                community_id="community_x", period="2024-01"
            )
            for anomaly in result["anomalies"]:
                assert anomaly["severity"] in valid_severities

    def test_flag_moderation_anomaly_high_severity_first(
        self, mock_anomaly_response
    ):
        """Test that high severity anomalies are prioritized."""
        with patch(
            "src.gated_communities.moderation_analytics._detect_anomalies",
            return_value=mock_anomaly_response,
        ):
            result = flag_moderation_anomaly(
                community_id="community_x", period="2024-01"
            )
            severities = [a["severity"] for a in result["anomalies"]]
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            sorted_severities = sorted(
                severities, key=lambda s: severity_order.get(s, 99)
            )
            assert severities == sorted_severities

    def test_flag_moderation_anomaly_no_anomalies(self):
        """Test handling when no anomalies are detected."""
        no_anomaly_response = {
            "status": "success",
            "data": {"anomalies_detected": 0, "anomalies": []},
        }
        with patch(
            "src.gated_communities.moderation_analytics._detect_anomalies",
            return_value=no_anomaly_response,
        ):
            result = flag_moderation_anomaly(
                community_id="community_a", period="2024-01"
            )
            assert result["anomalies_detected"] == 0
            assert result["anomalies"] == []

    def test_flag_moderation_anomaly_with_custom_thresholds(self):
        """Test anomaly detection with custom thresholds."""
        custom_response = {
            "status": "success",
            "data": {
                "anomalies_detected": 1,
                "anomalies": [
                    {
                        "id": "anomaly_custom",
                        "type": "spike_in_flags",
                        "severity": "medium",
                        "community": "community_y",
                        "timestamp": "2024-01-15T14:30:00Z",
                        "expected_value": 100,
                        "actual_value": 250,
                        "deviation_factor": 2.5,
                    }
                ],
            },
        }
        with patch(
            "src.gated_communities.moderation_analytics._detect_anomalies",
            return_value=custom_response,
        ) as mock_detect:
            result = flag_moderation_anomaly(
                community_id="community_y",
                period="2024-01",
                thresholds={"zscore": 2.0, "deviation": 0.2},
            )
            assert result["anomalies_detected"] == 1
            mock_detect.assert_called_once()

    def test_flag_moderation_anomaly_deviation_factor_calculation(
        self, mock_anomaly_response
    ):
        """Test that deviation factor is correctly calculated."""
        with patch(
            "src.gated_communities.moderation_analytics._detect_anomalies",
            return_value=mock_anomaly_response,
        ):
            result = flag_moderation_anomaly(
                community_id="community_x", period="2024-01"
            )
            for anomaly in result["anomalies"]:
                expected_deviation = (
                    anomaly["actual_value"] / anomaly["expected_value"]
                    if anomaly["expected_value"] != 0
                    else float("inf")
                )
                assert (
                    abs(anomaly["deviation_factor"] - expected_deviation) < 0.01
                )

    def test_flag_moderation_anomaly_community_filtering(
        self, mock_anomaly_response
    ):
        """Test that anomalies are filtered by community."""
        with patch(
            "src.gated_communities.moderation_analytics._detect_anomalies",
            return_value=mock_anomaly_response,
        ) as mock_detect:
            result = flag_moderation_anomaly(
                community_id="community_x", period="2024-01"
            )
            mock_detect.assert_called_once()
            call_args = mock_detect.call_args
            assert "community_x" in str(call_args)

    def test_flag_moderation_anomaly_invalid_community_raises_error(self):
        """Test that invalid community ID raises ValueError."""
        with pytest.raises(ValueError):
            flag_moderation_anomaly(community_id="", period="2024-01")

    def test_flag_moderation_anomaly_db_error_raises_exception(self):
        """Test that database errors are properly propagated."""
        with patch(
            "src.gated_communities.moderation_analytics._detect_anomalies",
            side_effect=ConnectionError("Database connection failed"),
        ):
            with pytest.raises(ConnectionError):
                flag_moderation_anomaly(
                    community_id="community_x", period="2024-01"
                )

    def test_flag_moderation_anomaly_timestamp_format(
        self, mock_anomaly_response
    ):
        """Test that anomaly timestamps are in valid ISO format."""
        with patch(
            "src.gated_communities.moderation_analytics._detect_anomalies",
            return_value=mock_anomaly_response,
        ):
            result = flag_moderation_anomaly(
                community_id="community_x", period="2024-01"
            )
            for anomaly in result["anomalies"]:
                # Should be parseable as ISO format
                datetime.fromisoformat(
                    anomaly["timestamp"].replace("Z", "+00:00")
                )

    def test_flag_moderation_anomaly_multiple_communities(self):
        """Test anomaly detection across multiple communities."""
        multi_community_response = {
            "status": "success",
            "data": {
                "anomalies_detected": 2,
                "anomalies": [
                    {
                        "id": "anomaly_1",
                        "type": "spike_in_flags",
                        "severity": "high",
                        "community": "community_a",
                        "timestamp": "2024-01-15T14:30:00Z",
                        "expected_value": 50,
                        "actual_value": 200,
                        "deviation_factor": 4.0,
                    },
                    {
                        "id": "anomaly_2",
                        "type": "resolution_rate_drop",
                        "severity": "medium",
                        "community": "community_b",
                        "timestamp": "2024-01-20T09:00:00Z",
                        "expected_value": 0.90,
                        "actual_value": 0.70,
                        "deviation_factor": 0.22,
                    },
                ],
            },
        }
        with patch(
            "src.gated_communities.moderation_analytics._detect_anomalies",
            return_value=multi_community_response,
        ):
            result = flag_moderation_anomaly(period="2024-01")
            assert result["anomalies_detected"] == 2
            communities = {a["community"] for a in result["anomalies"]}
            assert "community_a" in communities
            assert "community_b" in communities

    def test_flag_moderation_anomaly_anomaly_types_valid(
        self, mock_anomaly_response
    ):
        """Test that anomaly types are from valid set."""
        valid_types = {
            "spike_in_flags",
            "resolution_rate_drop",
            "resolution_time_surge",
            "unusual_moderator_activity",
            "coordinated_attack",
        }
        with patch(
            "src.gated_communities.moderation_analytics._detect_anomalies",
            return_value=mock_anomaly_response,
        ):
            result = flag_moderation_anomaly(
                community_id="community_x", period="2024-01"
            )
            for anomaly in result["anomalies"]:
                assert anomaly["type"] in valid_types

    def test_flag_moderation_anomaly_critical_severity_handling(self):
        """Test that critical severity anomalies are properly flagged."""
        critical_response = {
            "status": "success",
            "data": {
                "anomalies_detected": 1,
                "anomalies": [
                    {
                        "id": "anomaly_critical",
                        "type": "coordinated_attack",
                        "severity": "critical",
                        "community": "community_x",
                        "timestamp": "2024-01-15T14:30:00Z",
                        "expected_value": 10,
                        "actual_value": 500,
                        "deviation_factor": 50.0,
                    }
                ],
            },
        }
        with patch(
            "src.gated_communities.moderation_analytics._detect_anomalies",
            return_value=critical_response,
        ):
            result = flag_moderation_anomaly(
                community_id="community_x", period="2024-01"
            )
            assert result["anomalies"][0]["severity"] == "critical"
            assert result["anomalies"][0]["deviation_factor"] > 10.0
