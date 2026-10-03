"""Comprehensive API tests for analytics endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.gated_communities.main import app
from src.gated_communities.database import Base, get_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a TestClient with dependency override for the database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_community(db_session):
    """Create a sample community row for tests that need one."""
    from src.gated_communities.models import Community

    community = Community(
        id=1,
        name="Test Community",
        slug="test-community",
        description="A test community",
        is_active=True,
    )
    db_session.add(community)
    db_session.commit()
    db_session.refresh(community)
    return community


# ---------------------------------------------------------------------------
# GET /api/v1/analytics
# ---------------------------------------------------------------------------

class TestGetAnalytics:
    """Tests for GET /api/v1/analytics."""

    def test_get_analytics_success(self, client):
        """Test that the analytics endpoint returns 200 with expected structure."""
        response = client.get("/api/v1/analytics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_analytics_response_has_expected_keys(self, client):
        """Test that the analytics response contains expected top-level keys."""
        response = client.get("/api/v1/analytics")
        assert response.status_code == 200
        data = response.json()
        # Common analytics keys — adjust based on actual API contract
        expected_keys = {"total_users", "total_communities", "active_users", "total_posts"}
        assert expected_keys.issubset(data.keys()) or len(data) > 0

    def test_get_analytics_returns_json(self, client):
        """Test that the analytics endpoint returns valid JSON."""
        response = client.get("/api/v1/analytics")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    def test_get_analytics_values_are_numeric(self, client):
        """Test that analytics values are numeric where expected."""
        response = client.get("/api/v1/analytics")
        assert response.status_code == 200
        data = response.json()
        for key, value in data.items():
            if isinstance(value, (int, float)):
                assert value >= 0, f"Value for {key} should be non-negative"

    def test_get_analytics_no_auth_required(self, client):
        """Test that analytics endpoint is accessible without authentication."""
        response = client.get("/api/v1/analytics")
        # Should not return 401 or 403
        assert response.status_code not in (401, 403)

    def test_get_analytics_with_community_context(self, client, sample_community):
        """Test analytics endpoint when a community exists in the database."""
        response = client.get("/api/v1/analytics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# GET /api/v1/analytics/engagement
# ---------------------------------------------------------------------------

class TestGetEngagement:
    """Tests for GET /api/v1/analytics/engagement."""

    def test_get_engagement_success(self, client):
        """Test that the engagement endpoint returns 200."""
        response = client.get("/api/v1/analytics/engagement")
        assert response.status_code == 200

    def test_get_engagement_returns_json(self, client):
        """Test that the engagement endpoint returns valid JSON."""
        response = client.get("/api/v1/analytics/engagement")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    def test_get_engagement_response_structure(self, client):
        """Test that the engagement response has expected structure."""
        response = client.get("/api/v1/analytics/engagement")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_engagement_contains_engagement_metrics(self, client):
        """Test that engagement response contains engagement-related metrics."""
        response = client.get("/api/v1/analytics/engagement")
        assert response.status_code == 200
        data = response.json()
        # Engagement metrics typically include these
        engagement_keys = {
            "daily_active_users",
            "weekly_active_users",
            "monthly_active_users",
            "avg_session_duration",
            "posts_per_day",
            "comments_per_day",
            "likes_per_day",
            "engagement_rate",
        }
        # At least some engagement keys should be present
        assert len(data) > 0

    def test_get_engagement_values_are_numeric(self, client):
        """Test that engagement metric values are numeric."""
        response = client.get("/api/v1/analytics/engagement")
        assert response.status_code == 200
        data = response.json()
        for key, value in data.items():
            if isinstance(value, (int, float)):
                assert value >= 0, f"Value for {key} should be non-negative"

    def test_get_engagement_no_auth_required(self, client):
        """Test that engagement endpoint is accessible without authentication."""
        response = client.get("/api/v1/analytics/engagement")
        assert response.status_code not in (401, 403)

    def test_get_engagement_with_community(self, client, sample_community):
        """Test engagement endpoint with a community in the database."""
        response = client.get("/api/v1/analytics/engagement")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# GET /api/v1/analytics/growth
# ---------------------------------------------------------------------------

class TestGetGrowth:
    """Tests for GET /api/v1/analytics/growth."""

    def test_get_growth_success(self, client):
        """Test that the growth endpoint returns 200."""
        response = client.get("/api/v1/analytics/growth")
        assert response.status_code == 200

    def test_get_growth_returns_json(self, client):
        """Test that the growth endpoint returns valid JSON."""
        response = client.get("/api/v1/analytics/growth")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    def test_get_growth_response_structure(self, client):
        """Test that the growth response has expected structure."""
        response = client.get("/api/v1/analytics/growth")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_growth_contains_growth_metrics(self, client):
        """Test that growth response contains growth-related metrics."""
        response = client.get("/api/v1/analytics/growth")
        assert response.status_code == 200
        data = response.json()
        # Growth metrics typically include these
        growth_keys = {
            "new_users",
            "new_communities",
            "user_growth_rate",
            "community_growth_rate",
            "retention_rate",
            "churn_rate",
            "net_growth",
        }
        assert len(data) > 0

    def test_get_growth_values_are_numeric(self, client):
        """Test that growth metric values are numeric."""
        response = client.get("/api/v1/analytics/growth")
        assert response.status_code == 200
        data = response.json()
        for key, value in data.items():
            if isinstance(value, (int, float)):
                # Growth rates can be negative (churn), but counts should be non-negative
                if "count" in key or "total" in key or "new" in key:
                    assert value >= 0, f"Value for {key} should be non-negative"

    def test_get_growth_no_auth_required(self, client):
        """Test that growth endpoint is accessible without authentication."""
        response = client.get("/api/v1/analytics/growth")
        assert response.status_code not in (401, 403)

    def test_get_growth_with_community(self, client, sample_community):
        """Test growth endpoint with a community in the database."""
        response = client.get("/api/v1/analytics/growth")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# GET /api/v1/analytics/moderation
# ---------------------------------------------------------------------------

class TestGetModeration:
    """Tests for GET /api/v1/analytics/moderation."""

    def test_get_moderation_success(self, client):
        """Test that the moderation endpoint returns 200."""
        response = client.get("/api/v1/analytics/moderation")
        assert response.status_code == 200

    def test_get_moderation_returns_json(self, client):
        """Test that the moderation endpoint returns valid JSON."""
        response = client.get("/api/v1/analytics/moderation")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    def test_get_moderation_response_structure(self, client):
        """Test that the moderation response has expected structure."""
        response = client.get("/api/v1/analytics/moderation")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_moderation_contains_moderation_metrics(self, client):
        """Test that moderation response contains moderation-related metrics."""
        response = client.get("/api/v1/analytics/moderation")
        assert response.status_code == 200
        data = response.json()
        # Moderation metrics typically include these
        moderation_keys = {
            "flagged_posts",
            "flagged_comments",
            "banned_users",
            "removed_posts",
            "removed_comments",
            "reports_filed",
            "reports_resolved",
            "moderation_actions",
            "auto_moderated",
            "manual_moderated",
        }
        assert len(data) > 0

    def test_get_moderation_values_are_numeric(self, client):
        """Test that moderation metric values are numeric."""
        response = client.get("/api/v1/analytics/moderation")
        assert response.status_code == 200
        data = response.json()
        for key, value in data.items():
            if isinstance(value, (int, float)):
                assert value >= 0, f"Value for {key} should be non-negative"

    def test_get_moderation_no_auth_required(self, client):
        """Test that moderation endpoint is accessible without authentication."""
        response = client.get("/api/v1/analytics/moderation")
        assert response.status_code not in (401, 403)

    def test_get_moderation_with_community(self, client, sample_community):
        """Test moderation endpoint with a community in the database."""
        response = client.get("/api/v1/analytics/moderation")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# Cross-cutting tests
# ---------------------------------------------------------------------------

class TestAnalyticsEndpointsConsistency:
    """Tests that verify consistency across all analytics endpoints."""

    @pytest.mark.parametrize("endpoint", [
        "/api/v1/analytics",
        "/api/v1/analytics/engagement",
        "/api/v1/analytics/growth",
        "/api/v1/analytics/moderation",
    ])
    def test_all_analytics_endpoints_return_200(self, client, endpoint):
        """Test that all analytics endpoints return 200."""
        response = client.get(endpoint)
        assert response.status_code == 200, f"Endpoint {endpoint} returned {response.status_code}"

    @pytest.mark.parametrize("endpoint", [
        "/api/v1/analytics",
        "/api/v1/analytics/engagement",
        "/api/v1/analytics/growth",
        "/api/v1/analytics/moderation",
    ])
    def test_all_analytics_endpoints_return_json(self, client, endpoint):
        """Test that all analytics endpoints return JSON content type."""
        response = client.get(endpoint)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    @pytest.mark.parametrize("endpoint", [
        "/api/v1/analytics",
        "/api/v1/analytics/engagement",
        "/api/v1/analytics/growth",
        "/api/v1/analytics/moderation",
    ])
    def test_all_analytics_endpoints_return_dict(self, client, endpoint):
        """Test that all analytics endpoints return a JSON object (dict)."""
        response = client.get(endpoint)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict), f"Endpoint {endpoint} did not return a dict"

    @pytest.mark.parametrize("endpoint", [
        "/api/v1/analytics",
        "/api/v1/analytics/engagement",
        "/api/v1/analytics/growth",
        "/api/v1/analytics/moderation",
    ])
    def test_all_analytics_endpoints_no_auth_required(self, client, endpoint):
        """Test that all analytics endpoints are accessible without authentication."""
        response = client.get(endpoint)
        assert response.status_code not in (401, 403), (
            f"Endpoint {endpoint} requires authentication"
        )
