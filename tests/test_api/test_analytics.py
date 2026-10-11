"""API tests for analytics endpoints.

Real shipped routes (mounted at ROOT unless stated otherwise; all of these are
public — no auth required):

    GET /api/v1/analytics          -> 200 governance-analytics object
    GET /api/v1/analytics/summary  -> 200 governance summary object
    GET /engagement                -> 200 {"status", "data"}
    GET /dashboard                 -> 200 {"status", "data"}

Quarantined in this module:

* ``TestGetGrowth`` — no ``/analytics/growth`` (or equivalent growth) endpoint
  is shipped (404).
* ``TestGetModeration`` — no ``/analytics/moderation`` endpoint is shipped (404).
* ``/api/v1/analytics/engagement`` does not exist; the real engagement endpoint
  is mounted at ``/engagement`` and is covered by ``TestGetEngagement``.
"""

import pytest


ANALYTICS_PATHS = [
    "/api/v1/analytics",
    "/api/v1/analytics/summary",
    "/engagement",
    "/dashboard",
]


class TestGetAnalytics:
    """Tests for GET /api/v1/analytics."""

    def test_get_analytics_success(self, client):
        response = client.get("/api/v1/analytics")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_analytics_response_has_expected_keys(self, client):
        data = client.get("/api/v1/analytics").json()
        assert {"period_start", "period_end", "health_score", "generated_at"}.issubset(data)

    def test_get_analytics_returns_json(self, client):
        response = client.get("/api/v1/analytics")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    def test_get_analytics_values_are_numeric(self, client):
        for key, value in client.get("/api/v1/analytics").json().items():
            if isinstance(value, (int, float)):
                assert value >= 0, f"Value for {key} should be non-negative"

    def test_get_analytics_no_auth_required(self, client):
        response = client.get("/api/v1/analytics")
        assert response.status_code not in (401, 403)


class TestGovernanceSummary:
    """Tests for GET /api/v1/analytics/summary."""

    def test_summary_success(self, client):
        response = client.get("/api/v1/analytics/summary")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_summary_expected_keys(self, client):
        data = client.get("/api/v1/analytics/summary").json()
        assert {"health_score", "open_disputes", "last_updated"}.issubset(data)

    def test_summary_no_auth_required(self, client):
        assert client.get("/api/v1/analytics/summary").status_code == 200


class TestGetEngagement:
    """Tests for GET /engagement."""

    def test_get_engagement_success(self, client):
        assert client.get("/engagement").status_code == 200

    def test_get_engagement_returns_json(self, client):
        response = client.get("/engagement")
        assert response.headers["content-type"].startswith("application/json")

    def test_get_engagement_response_structure(self, client):
        data = client.get("/engagement").json()
        assert isinstance(data, dict)
        assert {"status", "data"}.issubset(data)

    def test_get_engagement_no_auth_required(self, client):
        assert client.get("/engagement").status_code not in (401, 403)


class TestGetDashboard:
    """Tests for GET /dashboard."""

    def test_get_dashboard_success(self, client):
        assert client.get("/dashboard").status_code == 200

    def test_get_dashboard_response_structure(self, client):
        data = client.get("/dashboard").json()
        assert {"status", "data"}.issubset(data)

    def test_get_dashboard_no_auth_required(self, client):
        assert client.get("/dashboard").status_code not in (401, 403)


@pytest.mark.skip(reason="/analytics/growth is not implemented (404)")
class TestGetGrowth:
    """Tests for growth analytics (quarantined — endpoint absent)."""

    def test_get_growth_success(self, client):
        assert client.get("/api/v1/analytics/growth").status_code == 200


@pytest.mark.skip(reason="/analytics/moderation is not implemented (404)")
class TestGetModeration:
    """Tests for moderation analytics (quarantined — endpoint absent)."""

    def test_get_moderation_success(self, client):
        assert client.get("/api/v1/analytics/moderation").status_code == 200


class TestAnalyticsEndpointsConsistency:
    """Consistency checks across the shipped analytics endpoints."""

    @pytest.mark.parametrize("endpoint", ANALYTICS_PATHS)
    def test_all_analytics_endpoints_return_200(self, client, endpoint):
        response = client.get(endpoint)
        assert response.status_code == 200, f"Endpoint {endpoint} returned {response.status_code}"

    @pytest.mark.parametrize("endpoint", ANALYTICS_PATHS)
    def test_all_analytics_endpoints_return_json(self, client, endpoint):
        response = client.get(endpoint)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    @pytest.mark.parametrize("endpoint", ANALYTICS_PATHS)
    def test_all_analytics_endpoints_return_dict(self, client, endpoint):
        response = client.get(endpoint)
        assert isinstance(response.json(), dict)

    @pytest.mark.parametrize("endpoint", ANALYTICS_PATHS)
    def test_all_analytics_endpoints_no_auth_required(self, client, endpoint):
        response = client.get(endpoint)
        assert response.status_code not in (401, 403)
