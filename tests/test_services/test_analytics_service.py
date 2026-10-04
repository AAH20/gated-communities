"""Comprehensive service tests for the analytics service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gated_communities.services.analytics_service import (
    AnalyticsService,
    get_community_metrics,
    get_engagement_metrics,
    get_growth_metrics,
    get_moderation_metrics,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Provide a mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest.fixture
def mock_cache():
    """Provide a mock cache client."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.exists = AsyncMock(return_value=False)
    return cache


@pytest.fixture
def analytics_service(mock_db, mock_cache):
    """Provide an AnalyticsService instance with mocked dependencies."""
    return AnalyticsService(db=mock_db, cache=mock_cache)


@pytest.fixture
def sample_community_id():
    """Return a sample community ID."""
    return "community-123"


@pytest.fixture
def sample_user_id():
    """Return a sample user ID."""
    return "user-456"


@pytest.fixture
def sample_date_range():
    """Return a sample date range for metrics queries."""
    end_date = datetime(2024, 6, 30, tzinfo=timezone.utc)
    start_date = end_date - timedelta(days=30)
    return start_date, end_date


@pytest.fixture
def sample_community_metrics():
    """Return sample community metrics data."""
    return {
        "community_id": "community-123",
        "total_members": 1500,
        "active_members": 875,
        "total_posts": 3200,
        "total_comments": 12800,
        "total_reactions": 25600,
        "new_members_this_month": 120,
        "churned_members_this_month": 45,
        "member_growth_rate": 0.085,
        "engagement_rate": 0.583,
        "avg_posts_per_user": 2.13,
        "avg_comments_per_post": 4.0,
        "avg_reactions_per_post": 8.0,
        "period_start": "2024-06-01T00:00:00+00:00",
        "period_end": "2024-06-30T00:00:00+00:00",
    }


@pytest.fixture
def sample_engagement_metrics():
    """Return sample engagement metrics data."""
    return {
        "community_id": "community-123",
        "daily_active_users": 320,
        "weekly_active_users": 875,
        "monthly_active_users": 1200,
        "avg_session_duration_minutes": 12.5,
        "avg_sessions_per_user": 3.2,
        "posts_created_today": 45,
        "comments_created_today": 180,
        "reactions_given_today": 720,
        "top_active_hours": [9, 12, 18, 20, 21],
        "engagement_trend": "increasing",
        "engagement_score": 78.5,
        "retention_rate_7d": 0.72,
        "retention_rate_30d": 0.55,
        "period_start": "2024-06-01T00:00:00+00:00",
        "period_end": "2024-06-30T00:00:00+00:00",
    }


@pytest.fixture
def sample_growth_metrics():
    """Return sample growth metrics data."""
    return {
        "community_id": "community-123",
        "total_members": 1500,
        "members_7d_ago": 1380,
        "members_30d_ago": 1200,
        "new_members_7d": 85,
        "new_members_30d": 120,
        "churned_members_7d": 20,
        "churned_members_30d": 45,
        "growth_rate_7d": 0.0616,
        "growth_rate_30d": 0.10,
        "net_growth_7d": 65,
        "net_growth_30d": 75,
        "projected_members_30d": 1650,
        "projected_members_90d": 1950,
        "acquisition_channels": {
            "invite": 45,
            "discovery": 30,
            "referral": 20,
            "direct": 25,
        },
        "period_start": "2024-06-01T00:00:00+00:00",
        "period_end": "2024-06-30T00:00:00+00:00",
    }


@pytest.fixture
def sample_moderation_metrics():
    """Return sample moderation metrics data."""
    return {
        "community_id": "community-123",
        "total_reports": 42,
        "pending_reports": 8,
        "resolved_reports": 30,
        "dismissed_reports": 4,
        "avg_resolution_time_hours": 4.5,
        "actions_taken": {
            "warning_issued": 15,
            "post_removed": 10,
            "user_muted": 5,
            "user_banned": 2,
        },
        "reports_by_category": {
            "spam": 12,
            "harassment": 8,
            "inappropriate_content": 15,
            "other": 7,
        },
        "moderation_actions_today": 5,
        "auto_moderated_count": 18,
        "false_positive_rate": 0.05,
        "period_start": "2024-06-01T00:00:00+00:00",
        "period_end": "2024-06-30T00:00:00+00:00",
    }


# ---------------------------------------------------------------------------
# Tests for get_community_metrics
# ---------------------------------------------------------------------------


class TestGetCommunityMetrics:
    """Tests for the get_community_metrics function."""

    @pytest.mark.asyncio
    async def test_get_community_metrics_returns_expected_data(
        self, analytics_service, sample_community_id, sample_date_range, sample_community_metrics
    ):
        """Test that get_community_metrics returns the expected metrics data."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_community_metrics",
            new_callable=AsyncMock,
            return_value=sample_community_metrics,
        ) as mock_get:
            result = await get_community_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result is not None
            assert result["community_id"] == sample_community_id
            assert result["total_members"] == 1500
            assert result["active_members"] == 875
            assert result["total_posts"] == 3200
            assert result["total_comments"] == 12800
            assert result["total_reactions"] == 25600
            assert result["new_members_this_month"] == 120
            assert result["churned_members_this_month"] == 45
            assert result["member_growth_rate"] == pytest.approx(0.085)
            assert result["engagement_rate"] == pytest.approx(0.583)
            assert result["avg_posts_per_user"] == pytest.approx(2.13)
            assert result["avg_comments_per_post"] == pytest.approx(4.0)
            assert result["avg_reactions_per_post"] == pytest.approx(8.0)

            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_community_metrics_with_default_dates(
        self, analytics_service, sample_community_id, sample_community_metrics
    ):
        """Test that get_community_metrics works with default date range."""
        with patch.object(
            analytics_service,
            "get_community_metrics",
            new_callable=AsyncMock,
            return_value=sample_community_metrics,
        ) as mock_get:
            result = await get_community_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
            )

            assert result is not None
            assert result["community_id"] == sample_community_id
            assert result["total_members"] == 1500
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_community_metrics_empty_result(
        self, analytics_service, sample_community_id, sample_date_range
    ):
        """Test that get_community_metrics handles empty results gracefully."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_community_metrics",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_get:
            result = await get_community_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result is None
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_community_metrics_caching(
        self, analytics_service, sample_community_id, sample_date_range, sample_community_metrics
    ):
        """Test that get_community_metrics uses caching when available."""
        start_date, end_date = sample_date_range
        analytics_service.cache.get = AsyncMock(return_value=sample_community_metrics)

        result = await get_community_metrics(
            db=analytics_service.db,
            community_id=sample_community_id,
            start_date=start_date,
            end_date=end_date,
        )

        assert result is not None
        assert result["community_id"] == sample_community_id
        analytics_service.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_community_metrics_cache_miss(
        self, analytics_service, sample_community_id, sample_date_range, sample_community_metrics
    ):
        """Test that get_community_metrics fetches from DB on cache miss."""
        start_date, end_date = sample_date_range
        analytics_service.cache.get = AsyncMock(return_value=None)

        with patch.object(
            analytics_service,
            "get_community_metrics",
            new_callable=AsyncMock,
            return_value=sample_community_metrics,
        ):
            result = await get_community_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result is not None
            analytics_service.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_community_metrics_invalid_community_id(
        self, analytics_service, sample_date_range
    ):
        """Test that get_community_metrics raises error for invalid community ID."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_community_metrics",
            new_callable=AsyncMock,
            side_effect=ValueError("Community not found"),
        ):
            with pytest.raises(ValueError, match="Community not found"):
                await get_community_metrics(
                    db=analytics_service.db,
                    community_id="",
                    start_date=start_date,
                    end_date=end_date,
                )

    @pytest.mark.asyncio
    async def test_get_community_metrics_db_error(
        self, analytics_service, sample_community_id, sample_date_range
    ):
        """Test that get_community_metrics handles database errors."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_community_metrics",
            new_callable=AsyncMock,
            side_effect=Exception("Database connection failed"),
        ):
            with pytest.raises(Exception, match="Database connection failed"):
                await get_community_metrics(
                    db=analytics_service.db,
                    community_id=sample_community_id,
                    start_date=start_date,
                    end_date=end_date,
                )

    @pytest.mark.asyncio
    async def test_get_community_metrics_data_types(
        self, analytics_service, sample_community_id, sample_date_range, sample_community_metrics
    ):
        """Test that get_community_metrics returns correct data types."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_community_metrics",
            new_callable=AsyncMock,
            return_value=sample_community_metrics,
        ):
            result = await get_community_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert isinstance(result["total_members"], int)
            assert isinstance(result["active_members"], int)
            assert isinstance(result["total_posts"], int)
            assert isinstance(result["total_comments"], int)
            assert isinstance(result["total_reactions"], int)
            assert isinstance(result["member_growth_rate"], float)
            assert isinstance(result["engagement_rate"], float)

    @pytest.mark.asyncio
    async def test_get_community_metrics_engagement_rate_calculation(
        self, analytics_service, sample_community_id, sample_date_range
    ):
        """Test that engagement rate is calculated correctly."""
        start_date, end_date = sample_date_range
        metrics = {
            "community_id": sample_community_id,
            "total_members": 1000,
            "active_members": 500,
            "engagement_rate": 0.5,
        }

        with patch.object(
            analytics_service,
            "get_community_metrics",
            new_callable=AsyncMock,
            return_value=metrics,
        ):
            result = await get_community_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result["engagement_rate"] == pytest.approx(0.5)
            assert result["active_members"] / result["total_members"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Tests for get_engagement_metrics
# ---------------------------------------------------------------------------


class TestGetEngagementMetrics:
    """Tests for the get_engagement_metrics function."""

    @pytest.mark.asyncio
    async def test_get_engagement_metrics_returns_expected_data(
        self, analytics_service, sample_community_id, sample_date_range, sample_engagement_metrics
    ):
        """Test that get_engagement_metrics returns the expected metrics data."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_engagement_metrics",
            new_callable=AsyncMock,
            return_value=sample_engagement_metrics,
        ) as mock_get:
            result = await get_engagement_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result is not None
            assert result["community_id"] == sample_community_id
            assert result["daily_active_users"] == 320
            assert result["weekly_active_users"] == 875
            assert result["monthly_active_users"] == 1200
            assert result["avg_session_duration_minutes"] == pytest.approx(12.5)
            assert result["avg_sessions_per_user"] == pytest.approx(3.2)
            assert result["posts_created_today"] == 45
            assert result["comments_created_today"] == 180
            assert result["reactions_given_today"] == 720
            assert result["top_active_hours"] == [9, 12, 18, 20, 21]
            assert result["engagement_trend"] == "increasing"
            assert result["engagement_score"] == pytest.approx(78.5)
            assert result["retention_rate_7d"] == pytest.approx(0.72)
            assert result["retention_rate_30d"] == pytest.approx(0.55)

            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_engagement_metrics_with_default_dates(
        self, analytics_service, sample_community_id, sample_engagement_metrics
    ):
        """Test that get_engagement_metrics works with default date range."""
        with patch.object(
            analytics_service,
            "get_engagement_metrics",
            new_callable=AsyncMock,
            return_value=sample_engagement_metrics,
        ) as mock_get:
            result = await get_engagement_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
            )

            assert result is not None
            assert result["community_id"] == sample_community_id
            assert result["daily_active_users"] == 320
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_engagement_metrics_empty_result(
        self, analytics_service, sample_community_id, sample_date_range
    ):
        """Test that get_engagement_metrics handles empty results gracefully."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_engagement_metrics",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_get:
            result = await get_engagement_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result is None
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_engagement_metrics_caching(
        self, analytics_service, sample_community_id, sample_date_range, sample_engagement_metrics
    ):
        """Test that get_engagement_metrics uses caching when available."""
        start_date, end_date = sample_date_range
        analytics_service.cache.get = AsyncMock(return_value=sample_engagement_metrics)

        result = await get_engagement_metrics(
            db=analytics_service.db,
            community_id=sample_community_id,
            start_date=start_date,
            end_date=end_date,
        )

        assert result is not None
        assert result["community_id"] == sample_community_id
        analytics_service.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_engagement_metrics_cache_miss(
        self, analytics_service, sample_community_id, sample_date_range, sample_engagement_metrics
    ):
        """Test that get_engagement_metrics fetches from DB on cache miss."""
        start_date, end_date = sample_date_range
        analytics_service.cache.get = AsyncMock(return_value=None)

        with patch.object(
            analytics_service,
            "get_engagement_metrics",
            new_callable=AsyncMock,
            return_value=sample_engagement_metrics,
        ):
            result = await get_engagement_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result is not None
            analytics_service.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_engagement_metrics_invalid_community_id(
        self, analytics_service, sample_date_range
    ):
        """Test that get_engagement_metrics raises error for invalid community ID."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_engagement_metrics",
            new_callable=AsyncMock,
            side_effect=ValueError("Community not found"),
        ):
            with pytest.raises(ValueError, match="Community not found"):
                await get_engagement_metrics(
                    db=analytics_service.db,
                    community_id="",
                    start_date=start_date,
                    end_date=end_date,
                )

    @pytest.mark.asyncio
    async def test_get_engagement_metrics_db_error(
        self, analytics_service, sample_community_id, sample_date_range
    ):
        """Test that get_engagement_metrics handles database errors."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_engagement_metrics",
            new_callable=AsyncMock,
            side_effect=Exception("Database connection failed"),
        ):
            with pytest.raises(Exception, match="Database connection failed"):
                await get_engagement_metrics(
                    db=analytics_service.db,
                    community_id=sample_community_id,
                    start_date=start_date,
                    end_date=end_date,
                )

    @pytest.mark.asyncio
    async def test_get_engagement_metrics_data_types(
        self, analytics_service, sample_community_id, sample_date_range, sample_engagement_metrics
    ):
        """Test that get_engagement_metrics returns correct data types."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_engagement_metrics",
            new_callable=AsyncMock,
            return_value=sample_engagement_metrics,
        ):
            result = await get_engagement_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert isinstance(result["daily_active_users"], int)
            assert isinstance(result["weekly_active_users"], int)
            assert isinstance(result["monthly_active_users"], int)
            assert isinstance(result["avg_session_duration_minutes"], float)
            assert isinstance(result["avg_sessions_per_user"], float)
            assert isinstance(result["engagement_score"], float)
            assert isinstance(result["retention_rate_7d"], float)
            assert isinstance(result["retention_rate_30d"], float)
            assert isinstance(result["top_active_hours"], list)

    @pytest.mark.asyncio
    async def test_get_engagement_metrics_retention_rates_valid_range(
        self, analytics_service, sample_community_id, sample_date_range
    ):
        """Test that retention rates are within valid range [0, 1]."""
        start_date, end_date = sample_date_range
        metrics = {
            "community_id": sample_community_id,
            "retention_rate_7d": 0.72,
            "retention_rate_30d": 0.55,
        }

        with patch.object(
            analytics_service,
            "get_engagement_metrics",
            new_callable=AsyncMock,
            return_value=metrics,
        ):
            result = await get_engagement_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert 0 <= result["retention_rate_7d"] <= 1
            assert 0 <= result["retention_rate_30d"] <= 1

    @pytest.mark.asyncio
    async def test_get_engagement_metrics_engagement_score_range(
        self, analytics_service, sample_community_id, sample_date_range
    ):
        """Test that engagement score is within valid range [0, 100]."""
        start_date, end_date = sample_date_range
        metrics = {
            "community_id": sample_community_id,
            "engagement_score": 78.5,
        }

        with patch.object(
            analytics_service,
            "get_engagement_metrics",
            new_callable=AsyncMock,
            return_value=metrics,
        ):
            result = await get_engagement_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert 0 <= result["engagement_score"] <= 100


# ---------------------------------------------------------------------------
# Tests for get_growth_metrics
# ---------------------------------------------------------------------------


class TestGetGrowthMetrics:
    """Tests for the get_growth_metrics function."""

    @pytest.mark.asyncio
    async def test_get_growth_metrics_returns_expected_data(
        self, analytics_service, sample_community_id, sample_date_range, sample_growth_metrics
    ):
        """Test that get_growth_metrics returns the expected metrics data."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_growth_metrics",
            new_callable=AsyncMock,
            return_value=sample_growth_metrics,
        ) as mock_get:
            result = await get_growth_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result is not None
            assert result["community_id"] == sample_community_id
            assert result["total_members"] == 1500
            assert result["members_7d_ago"] == 1380
            assert result["members_30d_ago"] == 1200
            assert result["new_members_7d"] == 85
            assert result["new_members_30d"] == 120
            assert result["churned_members_7d"] == 20
            assert result["churned_members_30d"] == 45
            assert result["growth_rate_7d"] == pytest.approx(0.0616)
            assert result["growth_rate_30d"] == pytest.approx(0.10)
            assert result["net_growth_7d"] == 65
            assert result["net_growth_30d"] == 75
            assert result["projected_members_30d"] == 1650
            assert result["projected_members_90d"] == 1950
            assert result["acquisition_channels"] == {
                "invite": 45,
                "discovery": 30,
                "referral": 20,
                "direct": 25,
            }

            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_growth_metrics_with_default_dates(
        self, analytics_service, sample_community_id, sample_growth_metrics
    ):
        """Test that get_growth_metrics works with default date range."""
        with patch.object(
            analytics_service,
            "get_growth_metrics",
            new_callable=AsyncMock,
            return_value=sample_growth_metrics,
        ) as mock_get:
            result = await get_growth_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
            )

            assert result is not None
            assert result["community_id"] == sample_community_id
            assert result["total_members"] == 1500
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_growth_metrics_empty_result(
        self, analytics_service, sample_community_id, sample_date_range
    ):
        """Test that get_growth_metrics handles empty results gracefully."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_growth_metrics",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_get:
            result = await get_growth_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result is None
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_growth_metrics_caching(
        self, analytics_service, sample_community_id, sample_date_range, sample_growth_metrics
    ):
        """Test that get_growth_metrics uses caching when available."""
        start_date, end_date = sample_date_range
        analytics_service.cache.get = AsyncMock(return_value=sample_growth_metrics)

        result = await get_growth_metrics(
            db=analytics_service.db,
            community_id=sample_community_id,
            start_date=start_date,
            end_date=end_date,
        )

        assert result is not None
        assert result["community_id"] == sample_community_id
        analytics_service.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_growth_metrics_cache_miss(
        self, analytics_service, sample_community_id, sample_date_range, sample_growth_metrics
    ):
        """Test that get_growth_metrics fetches from DB on cache miss."""
        start_date, end_date = sample_date_range
        analytics_service.cache.get = AsyncMock(return_value=None)

        with patch.object(
            analytics_service,
            "get_growth_metrics",
            new_callable=AsyncMock,
            return_value=sample_growth_metrics,
        ):
            result = await get_growth_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result is not None
            analytics_service.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_growth_metrics_invalid_community_id(
        self, analytics_service, sample_date_range
    ):
        """Test that get_growth_metrics raises error for invalid community ID."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_growth_metrics",
            new_callable=AsyncMock,
            side_effect=ValueError("Community not found"),
        ):
            with pytest.raises(ValueError, match="Community not found"):
                await get_growth_metrics(
                    db=analytics_service.db,
                    community_id="",
                    start_date=start_date,
                    end_date=end_date,
                )

    @pytest.mark.asyncio
    async def test_get_growth_metrics_db_error(
        self, analytics_service, sample_community_id, sample_date_range
    ):
        """Test that get_growth_metrics handles database errors."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_growth_metrics",
            new_callable=AsyncMock,
            side_effect=Exception("Database connection failed"),
        ):
            with pytest.raises(Exception, match="Database connection failed"):
                await get_growth_metrics(
                    db=analytics_service.db,
                    community_id=sample_community_id,
                    start_date=start_date,
                    end_date=end_date,
                )

    @pytest.mark.asyncio
    async def test_get_growth_metrics_data_types(
        self, analytics_service, sample_community_id, sample_date_range, sample_growth_metrics
    ):
        """Test that get_growth_metrics returns correct data types."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_growth_metrics",
            new_callable=AsyncMock,
            return_value=sample_growth_metrics,
        ):
            result = await get_growth_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert isinstance(result["total_members"], int)
            assert isinstance(result["new_members_7d"], int)
            assert isinstance(result["new_members_30d"], int)
            assert isinstance(result["churned_members_7d"], int)
            assert isinstance(result["churned_members_30d"], int)
            assert isinstance(result["growth_rate_7d"], float)
            assert isinstance(result["growth_rate_30d"], float)
            assert isinstance(result["net_growth_7d"], int)
            assert isinstance(result["net_growth_30d"], int)
            assert isinstance(result["acquisition_channels"], dict)

    @pytest.mark.asyncio
    async def test_get_growth_metrics_net_growth_calculation(
        self, analytics_service, sample_community_id, sample_date_range
    ):
        """Test that net growth is calculated correctly."""
        start_date, end_date = sample_date_range
        metrics = {
            "community_id": sample_community_id,
            "new_members_7d": 85,
            "churned_members_7d": 20,
            "net_growth_7d": 65,
        }

        with patch.object(
            analytics_service,
            "get_growth_metrics",
            new_callable=AsyncMock,
            return_value=metrics,
        ):
            result = await get_growth_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result["net_growth_7d"] == result["new_members_7d"] - result["churned_members_7d"]

    @pytest.mark.asyncio
    async def test_get_growth_metrics_acquisition_channels_sum(
        self, analytics_service, sample_community_id, sample_date_range, sample_growth_metrics
    ):
        """Test that acquisition channels sum to total new members."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_growth_metrics",
            new_callable=AsyncMock,
            return_value=sample_growth_metrics,
        ):
            result = await get_growth_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            total_from_channels = sum(result["acquisition_channels"].values())
            assert total_from_channels == result["new_members_30d"]


# ---------------------------------------------------------------------------
# Tests for get_moderation_metrics
# ---------------------------------------------------------------------------


class TestGetModerationMetrics:
    """Tests for the get_moderation_metrics function."""

    @pytest.mark.asyncio
    async def test_get_moderation_metrics_returns_expected_data(
        self, analytics_service, sample_community_id, sample_date_range, sample_moderation_metrics
    ):
        """Test that get_moderation_metrics returns the expected metrics data."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_moderation_metrics",
            new_callable=AsyncMock,
            return_value=sample_moderation_metrics,
        ) as mock_get:
            result = await get_moderation_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result is not None
            assert result["community_id"] == sample_community_id
            assert result["total_reports"] == 42
            assert result["pending_reports"] == 8
            assert result["resolved_reports"] == 30
            assert result["dismissed_reports"] == 4
            assert result["avg_resolution_time_hours"] == pytest.approx(4.5)
            assert result["actions_taken"] == {
                "warning_issued": 15,
                "post_removed": 10,
                "user_muted": 5,
                "user_banned": 2,
            }
            assert result["reports_by_category"] == {
                "spam": 12,
                "harassment": 8,
                "inappropriate_content": 15,
                "other": 7,
            }
            assert result["moderation_actions_today"] == 5
            assert result["auto_moderated_count"] == 18
            assert result["false_positive_rate"] == pytest.approx(0.05)

            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_moderation_metrics_with_default_dates(
        self, analytics_service, sample_community_id, sample_moderation_metrics
    ):
        """Test that get_moderation_metrics works with default date range."""
        with patch.object(
            analytics_service,
            "get_moderation_metrics",
            new_callable=AsyncMock,
            return_value=sample_moderation_metrics,
        ) as mock_get:
            result = await get_moderation_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
            )

            assert result is not None
            assert result["community_id"] == sample_community_id
            assert result["total_reports"] == 42
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_moderation_metrics_empty_result(
        self, analytics_service, sample_community_id, sample_date_range
    ):
        """Test that get_moderation_metrics handles empty results gracefully."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_moderation_metrics",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_get:
            result = await get_moderation_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result is None
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_moderation_metrics_caching(
        self, analytics_service, sample_community_id, sample_date_range, sample_moderation_metrics
    ):
        """Test that get_moderation_metrics uses caching when available."""
        start_date, end_date = sample_date_range
        analytics_service.cache.get = AsyncMock(return_value=sample_moderation_metrics)

        result = await get_moderation_metrics(
            db=analytics_service.db,
            community_id=sample_community_id,
            start_date=start_date,
            end_date=end_date,
        )

        assert result is not None
        assert result["community_id"] == sample_community_id
        analytics_service.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_moderation_metrics_cache_miss(
        self, analytics_service, sample_community_id, sample_date_range, sample_moderation_metrics
    ):
        """Test that get_moderation_metrics fetches from DB on cache miss."""
        start_date, end_date = sample_date_range
        analytics_service.cache.get = AsyncMock(return_value=None)

        with patch.object(
            analytics_service,
            "get_moderation_metrics",
            new_callable=AsyncMock,
            return_value=sample_moderation_metrics,
        ):
            result = await get_moderation_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result is not None
            analytics_service.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_moderation_metrics_invalid_community_id(
        self, analytics_service, sample_date_range
    ):
        """Test that get_moderation_metrics raises error for invalid community ID."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_moderation_metrics",
            new_callable=AsyncMock,
            side_effect=ValueError("Community not found"),
        ):
            with pytest.raises(ValueError, match="Community not found"):
                await get_moderation_metrics(
                    db=analytics_service.db,
                    community_id="",
                    start_date=start_date,
                    end_date=end_date,
                )

    @pytest.mark.asyncio
    async def test_get_moderation_metrics_db_error(
        self, analytics_service, sample_community_id, sample_date_range
    ):
        """Test that get_moderation_metrics handles database errors."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_moderation_metrics",
            new_callable=AsyncMock,
            side_effect=Exception("Database connection failed"),
        ):
            with pytest.raises(Exception, match="Database connection failed"):
                await get_moderation_metrics(
                    db=analytics_service.db,
                    community_id=sample_community_id,
                    start_date=start_date,
                    end_date=end_date,
                )

    @pytest.mark.asyncio
    async def test_get_moderation_metrics_data_types(
        self, analytics_service, sample_community_id, sample_date_range, sample_moderation_metrics
    ):
        """Test that get_moderation_metrics returns correct data types."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_moderation_metrics",
            new_callable=AsyncMock,
            return_value=sample_moderation_metrics,
        ):
            result = await get_moderation_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert isinstance(result["total_reports"], int)
            assert isinstance(result["pending_reports"], int)
            assert isinstance(result["resolved_reports"], int)
            assert isinstance(result["dismissed_reports"], int)
            assert isinstance(result["avg_resolution_time_hours"], float)
            assert isinstance(result["actions_taken"], dict)
            assert isinstance(result["reports_by_category"], dict)
            assert isinstance(result["moderation_actions_today"], int)
            assert isinstance(result["auto_moderated_count"], int)
            assert isinstance(result["false_positive_rate"], float)

    @pytest.mark.asyncio
    async def test_get_moderation_metrics_report_totals(
        self, analytics_service, sample_community_id, sample_date_range, sample_moderation_metrics
    ):
        """Test that report totals add up correctly."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_moderation_metrics",
            new_callable=AsyncMock,
            return_value=sample_moderation_metrics,
        ):
            result = await get_moderation_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            total_from_statuses = (
                result["pending_reports"]
                + result["resolved_reports"]
                + result["dismissed_reports"]
            )
            assert total_from_statuses == result["total_reports"]

    @pytest.mark.asyncio
    async def test_get_moderation_metrics_category_totals(
        self, analytics_service, sample_community_id, sample_date_range, sample_moderation_metrics
    ):
        """Test that report categories sum to total reports."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_moderation_metrics",
            new_callable=AsyncMock,
            return_value=sample_moderation_metrics,
        ):
            result = await get_moderation_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            total_from_categories = sum(result["reports_by_category"].values())
            assert total_from_categories == result["total_reports"]

    @pytest.mark.asyncio
    async def test_get_moderation_metrics_false_positive_rate_range(
        self, analytics_service, sample_community_id, sample_date_range
    ):
        """Test that false positive rate is within valid range [0, 1]."""
        start_date, end_date = sample_date_range
        metrics = {
            "community_id": sample_community_id,
            "false_positive_rate": 0.05,
        }

        with patch.object(
            analytics_service,
            "get_moderation_metrics",
            new_callable=AsyncMock,
            return_value=metrics,
        ):
            result = await get_moderation_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert 0 <= result["false_positive_rate"] <= 1

    @pytest.mark.asyncio
    async def test_get_moderation_metrics_action_totals(
        self, analytics_service, sample_community_id, sample_date_range, sample_moderation_metrics
    ):
        """Test that action totals are consistent."""
        start_date, end_date = sample_date_range

        with patch.object(
            analytics_service,
            "get_moderation_metrics",
            new_callable=AsyncMock,
            return_value=sample_moderation_metrics,
        ):
            result = await get_moderation_metrics(
                db=analytics_service.db,
                community_id=sample_community_id,
                start_date=start_date,
                end_date=end_date,
            )

            total_actions = sum(result["actions_taken"].values())
            assert total_actions == result["resolved_reports"] + result["dismissed_reports"]
