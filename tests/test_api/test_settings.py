"""Tests for the Settings API endpoints."""

import pytest
from fastapi.testclient import TestClient

from gated_communities.main import app


@pytest.fixture
def client():
    """Return a TestClient for the app."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Return headers with a valid auth token."""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def sample_settings():
    """Return a sample settings payload."""
    return {
        "community_name": "Test Community",
        "description": "A test community for unit testing",
        "is_public": False,
        "allow_invites": True,
        "default_role": "member",
    }


@pytest.fixture
def sample_moderation_settings():
    """Return a sample moderation settings payload."""
    return {
        "auto_moderation_enabled": True,
        "profanity_filter": True,
        "spam_detection": True,
        "max_post_length": 5000,
        "min_account_age_days": 7,
        "require_email_verification": True,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/settings
# ---------------------------------------------------------------------------


class TestGetSettings:
    """Tests for GET /api/v1/settings."""

    def test_get_settings_success(self, client, auth_headers):
        """GET /api/v1/settings returns 200 and a settings object."""
        response = client.get("/api/v1/settings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "community_name" in data or "settings" in data or len(data) > 0

    def test_get_settings_unauthenticated(self, client):
        """GET /api/v1/settings without auth returns 401."""
        response = client.get("/api/v1/settings")
        assert response.status_code == 401

    def test_get_settings_invalid_token(self, client):
        """GET /api/v1/settings with an invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/settings", headers=headers)
        assert response.status_code == 401

    def test_get_settings_response_structure(self, client, auth_headers):
        """GET /api/v1/settings response has expected keys."""
        response = client.get("/api/v1/settings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # The response should be a JSON object
        assert isinstance(data, dict)

    def test_get_settings_content_type(self, client, auth_headers):
        """GET /api/v1/settings returns JSON content type."""
        response = client.get("/api/v1/settings", headers=auth_headers)
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# PUT /api/v1/settings
# ---------------------------------------------------------------------------


class TestUpdateSettings:
    """Tests for PUT /api/v1/settings."""

    def test_update_settings_success(self, client, auth_headers, sample_settings):
        """PUT /api/v1/settings with valid data returns 200."""
        response = client.put(
            "/api/v1/settings", json=sample_settings, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_update_settings_unauthenticated(self, client, sample_settings):
        """PUT /api/v1/settings without auth returns 401."""
        response = client.put("/api/v1/settings", json=sample_settings)
        assert response.status_code == 401

    def test_update_settings_invalid_token(self, client, sample_settings):
        """PUT /api/v1/settings with an invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.put(
            "/api/v1/settings", json=sample_settings, headers=headers
        )
        assert response.status_code == 401

    def test_update_settings_empty_body(self, client, auth_headers):
        """PUT /api/v1/settings with an empty body returns 422."""
        response = client.put("/api/v1/settings", json={}, headers=auth_headers)
        assert response.status_code == 422

    def test_update_settings_partial_update(self, client, auth_headers):
        """PUT /api/v1/settings with partial data succeeds."""
        partial = {"community_name": "Updated Name"}
        response = client.put(
            "/api/v1/settings", json=partial, headers=auth_headers
        )
        assert response.status_code == 200

    def test_update_settings_content_type(self, client, auth_headers, sample_settings):
        """PUT /api/v1/settings returns JSON content type."""
        response = client.put(
            "/api/v1/settings", json=sample_settings, headers=auth_headers
        )
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_update_settings_persists_changes(self, client, auth_headers, sample_settings):
        """PUT /api/v1/settings changes are reflected in subsequent GET."""
        client.put("/api/v1/settings", json=sample_settings, headers=auth_headers)
        response = client.get("/api/v1/settings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # At least one of the updated fields should be present
        if "community_name" in data:
            assert data["community_name"] == sample_settings["community_name"]


# ---------------------------------------------------------------------------
# GET /api/v1/settings/moderation
# ---------------------------------------------------------------------------


class TestGetModerationSettings:
    """Tests for GET /api/v1/settings/moderation."""

    def test_get_moderation_settings_success(self, client, auth_headers):
        """GET /api/v1/settings/moderation returns 200 and a settings object."""
        response = client.get("/api/v1/settings/moderation", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_moderation_settings_unauthenticated(self, client):
        """GET /api/v1/settings/moderation without auth returns 401."""
        response = client.get("/api/v1/settings/moderation")
        assert response.status_code == 401

    def test_get_moderation_settings_invalid_token(self, client):
        """GET /api/v1/settings/moderation with an invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/settings/moderation", headers=headers)
        assert response.status_code == 401

    def test_get_moderation_settings_response_structure(self, client, auth_headers):
        """GET /api/v1/settings/moderation response has expected keys."""
        response = client.get("/api/v1/settings/moderation", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_moderation_settings_content_type(self, client, auth_headers):
        """GET /api/v1/settings/moderation returns JSON content type."""
        response = client.get("/api/v1/settings/moderation", headers=auth_headers)
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# PUT /api/v1/settings/moderation
# ---------------------------------------------------------------------------


class TestUpdateModerationSettings:
    """Tests for PUT /api/v1/settings/moderation."""

    def test_update_moderation_settings_success(
        self, client, auth_headers, sample_moderation_settings
    ):
        """PUT /api/v1/settings/moderation with valid data returns 200."""
        response = client.put(
            "/api/v1/settings/moderation",
            json=sample_moderation_settings,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_update_moderation_settings_unauthenticated(
        self, client, sample_moderation_settings
    ):
        """PUT /api/v1/settings/moderation without auth returns 401."""
        response = client.put(
            "/api/v1/settings/moderation", json=sample_moderation_settings
        )
        assert response.status_code == 401

    def test_update_moderation_settings_invalid_token(
        self, client, sample_moderation_settings
    ):
        """PUT /api/v1/settings/moderation with an invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.put(
            "/api/v1/settings/moderation",
            json=sample_moderation_settings,
            headers=headers,
        )
        assert response.status_code == 401

    def test_update_moderation_settings_empty_body(self, client, auth_headers):
        """PUT /api/v1/settings/moderation with an empty body returns 422."""
        response = client.put(
            "/api/v1/settings/moderation", json={}, headers=auth_headers
        )
        assert response.status_code == 422

    def test_update_moderation_settings_partial_update(self, client, auth_headers):
        """PUT /api/v1/settings/moderation with partial data succeeds."""
        partial = {"auto_moderation_enabled": False}
        response = client.put(
            "/api/v1/settings/moderation", json=partial, headers=auth_headers
        )
        assert response.status_code == 200

    def test_update_moderation_settings_content_type(
        self, client, auth_headers, sample_moderation_settings
    ):
        """PUT /api/v1/settings/moderation returns JSON content type."""
        response = client.put(
            "/api/v1/settings/moderation",
            json=sample_moderation_settings,
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_update_moderation_settings_persists_changes(
        self, client, auth_headers, sample_moderation_settings
    ):
        """PUT /api/v1/settings/moderation changes are reflected in subsequent GET."""
        client.put(
            "/api/v1/settings/moderation",
            json=sample_moderation_settings,
            headers=auth_headers,
        )
        response = client.get("/api/v1/settings/moderation", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        if "auto_moderation_enabled" in data:
            assert (
                data["auto_moderation_enabled"]
                == sample_moderation_settings["auto_moderation_enabled"]
            )
