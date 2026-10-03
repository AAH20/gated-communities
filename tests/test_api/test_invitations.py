"""Comprehensive API tests for the Invitations endpoints.

Covers:
  - GET    /api/v1/invitations          (list with pagination)
  - POST   /api/v1/invitations          (create)
  - GET    /api/v1/invitations/{id}     (retrieve)
  - PUT    /api/v1/invitations/{id}     (update)
  - DELETE /api/v1/invitations/{id}     (delete)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI TestClient bound to the application."""
    # Import here so the app is only loaded when tests run.
    from src.gated_communities.main import app

    return TestClient(app)


@pytest.fixture
def sample_invitation_payload() -> Dict[str, Any]:
    """Return a valid payload for creating an invitation."""
    return {
        "email": "invitee@example.com",
        "role": "member",
        "community_id": "comm-123",
        "message": "Join our community!",
    }


@pytest.fixture
def created_invitation(
    client: TestClient, sample_invitation_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Create an invitation via the API and return the response body."""
    response = client.post(
        "/api/v1/invitations",
        json=sample_invitation_payload,
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def multiple_invitations(client: TestClient) -> List[Dict[str, Any]]:
    """Create several invitations and return their response bodies."""
    invitations: List[Dict[str, Any]] = []
    for i in range(5):
        payload = {
            "email": f"user{i}@example.com",
            "role": "member",
            "community_id": f"comm-{i}",
            "message": f"Invitation #{i}",
        }
        response = client.post("/api/v1/invitations", json=payload)
        assert response.status_code == 201, response.text
        invitations.append(response.json())
    return invitations


# ---------------------------------------------------------------------------
# 1. GET /api/v1/invitations  — list with pagination
# ---------------------------------------------------------------------------


class TestListInvitations:
    """Tests for the list-invitations endpoint."""

    def test_list_invitations_returns_200(self, client: TestClient) -> None:
        """GET /api/v1/invitations returns HTTP 200."""
        response = client.get("/api/v1/invitations")
        assert response.status_code == 200

    def test_list_invitations_returns_list(
        self, client: TestClient, multiple_invitations: List[Dict[str, Any]]
    ) -> None:
        """Response body is a JSON list containing all created invitations."""
        response = client.get("/api/v1/invitations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= len(multiple_invitations)

    def test_list_invitations_empty(self, client: TestClient) -> None:
        """When no invitations exist the endpoint returns an empty list."""
        # NOTE: This test assumes a clean database.  If the test suite
        # shares state, consider using a fixture that clears the table.
        response = client.get("/api/v1/invitations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_invitations_pagination_limit(
        self, client: TestClient, multiple_invitations: List[Dict[str, Any]]
    ) -> None:
        """The `limit` query parameter caps the number of returned items."""
        limit = 2
        response = client.get(f"/api/v1/invitations?limit={limit}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= limit

    def test_list_invitations_pagination_offset(
        self, client: TestClient, multiple_invitations: List[Dict[str, Any]]
    ) -> None:
        """The `offset` query parameter skips the first N items."""
        # Fetch all invitations
        all_response = client.get("/api/v1/invitations?limit=100")
        all_data = all_response.json()
        total = len(all_data)

        if total < 2:
            pytest.skip("Need at least 2 invitations to test offset")

        offset = 1
        response = client.get(f"/api/v1/invitations?offset={offset}&limit=100")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == total - offset

    def test_list_invitations_pagination_combined(
        self, client: TestClient, multiple_invitations: List[Dict[str, Any]]
    ) -> None:
        """`limit` and `offset` work together for paginated browsing."""
        page_size = 2
        page = 1
        response = client.get(
            f"/api/v1/invitations?limit={page_size}&offset={page * page_size}"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= page_size

    def test_list_invitations_invalid_limit_returns_error(
        self, client: TestClient
    ) -> None:
        """A negative `limit` is rejected with a 422 validation error."""
        response = client.get("/api/v1/invitations?limit=-1")
        assert response.status_code == 422

    def test_list_invitations_invalid_offset_returns_error(
        self, client: TestClient
    ) -> None:
        """A negative `offset` is rejected with a 422 validation error."""
        response = client.get("/api/v1/invitations?offset=-5")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 2. POST /api/v1/invitations  — create
# ---------------------------------------------------------------------------


class TestCreateInvitation:
    """Tests for the create-invitation endpoint."""

    def test_create_invitation_returns_201(
        self, client: TestClient, sample_invitation_payload: Dict[str, Any]
    ) -> None:
        """POST /api/v1/invitations returns HTTP 201 on success."""
        response = client.post(
            "/api/v1/invitations",
            json=sample_invitation_payload,
        )
        assert response.status_code == 201

    def test_create_invitation_response_body(
        self, client: TestClient, sample_invitation_payload: Dict[str, Any]
    ) -> None:
        """The response body echoes back the created invitation fields."""
        response = client.post(
            "/api/v1/invitations",
            json=sample_invitation_payload,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_invitation_payload["email"]
        assert data["role"] == sample_invitation_payload["role"]
        assert data["community_id"] == sample_invitation_payload["community_id"]
        assert "id" in data

    def test_create_invitation_persists(
        self, client: TestClient, sample_invitation_payload: Dict[str, Any]
    ) -> None:
        """A created invitation is retrievable via the list endpoint."""
        create_response = client.post(
            "/api/v1/invitations",
            json=sample_invitation_payload,
        )
        assert create_response.status_code == 201
        created = create_response.json()

        list_response = client.get("/api/v1/invitations?limit=100")
        assert list_response.status_code == 200
        all_invitations = list_response.json()
        ids = [inv["id"] for inv in all_invitations]
        assert created["id"] in ids

    def test_create_invitation_missing_email_returns_422(
        self, client: TestClient
    ) -> None:
        """Omitting the required `email` field yields a 422 error."""
        payload = {
            "role": "member",
            "community_id": "comm-123",
        }
        response = client.post("/api/v1/invitations", json=payload)
        assert response.status_code == 422

    def test_create_invitation_missing_role_returns_422(
        self, client: TestClient
    ) -> None:
        """Omitting the required `role` field yields a 422 error."""
        payload = {
            "email": "test@example.com",
            "community_id": "comm-123",
        }
        response = client.post("/api/v1/invitations", json=payload)
        assert response.status_code == 422

    def test_create_invitation_invalid_email_returns_422(
        self, client: TestClient
    ) -> None:
        """An invalid email address is rejected with a 422 error."""
        payload = {
            "email": "not-an-email",
            "role": "member",
            "community_id": "comm-123",
        }
        response = client.post("/api/v1/invitations", json=payload)
        assert response.status_code == 422

    def test_create_invitation_empty_body_returns_422(
        self, client: TestClient
    ) -> None:
        """An empty JSON body is rejected with a 422 error."""
        response = client.post("/api/v1/invitations", json={})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 3. GET /api/v1/invitations/{id}  — retrieve
# ---------------------------------------------------------------------------


class TestGetInvitation:
    """Tests for the get-invitation endpoint."""

    def test_get_invitation_returns_200(
        self, client: TestClient, created_invitation: Dict[str, Any]
    ) -> None:
        """GET /api/v1/invitations/{id} returns HTTP 200 for an existing invitation."""
        invitation_id = created_invitation["id"]
        response = client.get(f"/api/v1/invitations/{invitation_id}")
        assert response.status_code == 200

    def test_get_invitation_response_body(
        self, client: TestClient, created_invitation: Dict[str, Any]
    ) -> None:
        """The response body matches the created invitation."""
        invitation_id = created_invitation["id"]
        response = client.get(f"/api/v1/invitations/{invitation_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == invitation_id
        assert data["email"] == created_invitation["email"]
        assert data["role"] == created_invitation["role"]
        assert data["community_id"] == created_invitation["community_id"]

    def test_get_invitation_not_found_returns_404(
        self, client: TestClient
    ) -> None:
        """GET on a non-existent id returns HTTP 404."""
        response = client.get("/api/v1/invitations/nonexistent-id-99999")
        assert response.status_code == 404

    def test_get_invitation_invalid_id_format_returns_422(
        self, client: TestClient
    ) -> None:
        """An id that fails UUID validation returns HTTP 422."""
        response = client.get("/api/v1/invitations/not-a-uuid")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 4. PUT /api/v1/invitations/{id}  — update
# ---------------------------------------------------------------------------


class TestUpdateInvitation:
    """Tests for the update-invitation endpoint."""

    def test_update_invitation_returns_200(
        self, client: TestClient, created_invitation: Dict[str, Any]
    ) -> None:
        """PUT /api/v1/invitations/{id} returns HTTP 200 on success."""
        invitation_id = created_invitation["id"]
        update_payload = {"role": "admin"}
        response = client.put(
            f"/api/v1/invitations/{invitation_id}",
            json=update_payload,
        )
        assert response.status_code == 200

    def test_update_invitation_response_body(
        self, client: TestClient, created_invitation: Dict[str, Any]
    ) -> None:
        """The response body reflects the updated fields."""
        invitation_id = created_invitation["id"]
        update_payload = {"role": "moderator", "message": "Updated message"}
        response = client.put(
            f"/api/v1/invitations/{invitation_id}",
            json=update_payload,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == invitation_id
        assert data["role"] == "moderator"
        assert data["message"] == "Updated message"

    def test_update_invitation_persists(
        self, client: TestClient, created_invitation: Dict[str, Any]
    ) -> None:
        """An updated invitation reflects changes on subsequent GET."""
        invitation_id = created_invitation["id"]
        update_payload = {"role": "owner"}
        update_response = client.put(
            f"/api/v1/invitations/{invitation_id}",
            json=update_payload,
        )
        assert update_response.status_code == 200

        get_response = client.get(f"/api/v1/invitations/{invitation_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["role"] == "owner"

    def test_update_invitation_not_found_returns_404(
        self, client: TestClient
    ) -> None:
        """PUT on a non-existent id returns HTTP 404."""
        response = client.put(
            "/api/v1/invitations/nonexistent-id-99999",
            json={"role": "admin"},
        )
        assert response.status_code == 404

    def test_update_invitation_empty_body_returns_422(
        self, client: TestClient, created_invitation: Dict[str, Any]
    ) -> None:
        """An empty JSON body is rejected with a 422 error."""
        invitation_id = created_invitation["id"]
        response = client.put(
            f"/api/v1/invitations/{invitation_id}",
            json={},
        )
        assert response.status_code == 422

    def test_update_invitation_invalid_email_returns_422(
        self, client: TestClient, created_invitation: Dict[str, Any]
    ) -> None:
        """An invalid email in the update payload is rejected."""
        invitation_id = created_invitation["id"]
        response = client.put(
            f"/api/v1/invitations/{invitation_id}",
            json={"email": "bad-email"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 5. DELETE /api/v1/invitations/{id}  — delete
# ---------------------------------------------------------------------------


class TestDeleteInvitation:
    """Tests for the delete-invitation endpoint."""

    def test_delete_invitation_returns_204(
        self, client: TestClient, created_invitation: Dict[str, Any]
    ) -> None:
        """DELETE /api/v1/invitations/{id} returns HTTP 204 on success."""
        invitation_id = created_invitation["id"]
        response = client.delete(f"/api/v1/invitations/{invitation_id}")
        assert response.status_code == 204

    def test_delete_invitation_removes_from_store(
        self, client: TestClient, created_invitation: Dict[str, Any]
    ) -> None:
        """A deleted invitation is no longer retrievable."""
        invitation_id = created_invitation["id"]

        # Delete
        delete_response = client.delete(f"/api/v1/invitations/{invitation_id}")
        assert delete_response.status_code == 204

        # Verify it is gone
        get_response = client.get(f"/api/v1/invitations/{invitation_id}")
        assert get_response.status_code == 404

    def test_delete_invitation_not_found_returns_404(
        self, client: TestClient
    ) -> None:
        """DELETE on a non-existent id returns HTTP 404."""
        response = client.delete("/api/v1/invitations/nonexistent-id-99999")
        assert response.status_code == 404

    def test_delete_invitation_idempotent_behavior(
        self, client: TestClient, created_invitation: Dict[str, Any]
    ) -> None:
        """Deleting the same invitation twice: second call returns 404."""
        invitation_id = created_invitation["id"]

        first = client.delete(f"/api/v1/invitations/{invitation_id}")
        assert first.status_code == 204

        second = client.delete(f"/api/v1/invitations/{invitation_id}")
        assert second.status_code == 404

    def test_delete_invitation_invalid_id_format_returns_422(
        self, client: TestClient
    ) -> None:
        """An id that fails UUID validation returns HTTP 422."""
        response = client.delete("/api/v1/invitations/not-a-uuid")
        assert response.status_code == 422
