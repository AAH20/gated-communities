"""Comprehensive API tests for the Members endpoints.

Tests cover:
- GET    /api/v1/members       (list with pagination)
- POST   /api/v1/members       (create)
- GET    /api/v1/members/{id}  (retrieve)
- PUT    /api/v1/members/{id}  (update)
- DELETE /api/v1/members/{id}  (delete)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gated_communities.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client() -> TestClient:
    """Return a FastAPI TestClient bound to the application."""
    return TestClient(app)


@pytest.fixture()
def sample_member_payload() -> dict:
    """Return a valid payload for creating a member."""
    return {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "role": "member",
    }


@pytest.fixture()
def created_member(client: TestClient, sample_member_payload: dict) -> dict:
    """Create a member via the API and return the response body."""
    response = client.post("/api/v1/members", json=sample_member_payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# 1. GET /api/v1/members — list with pagination
# ---------------------------------------------------------------------------

class TestListMembers:
    """Tests for GET /api/v1/members."""

    def test_list_members_returns_200(self, client: TestClient) -> None:
        """Basic smoke test — endpoint returns 200."""
        response = client.get("/api/v1/members")
        assert response.status_code == 200

    def test_list_members_returns_list(self, client: TestClient) -> None:
        """Response JSON is a list."""
        response = client.get("/api/v1/members")
        assert isinstance(response.json(), list)

    def test_list_members_empty(self, client: TestClient) -> None:
        """When no members exist the list is empty."""
        response = client.get("/api/v1/members")
        assert response.json() == []

    def test_list_members_pagination_limit(
        self, client: TestClient, sample_member_payload: dict
    ) -> None:
        """The `limit` query parameter caps the number of returned items."""
        # Create 5 members
        for i in range(5):
            payload = {**sample_member_payload, "email": f"user{i}@example.com"}
            client.post("/api/v1/members", json=payload)

        response = client.get("/api/v1/members", params={"limit": 2})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_members_pagination_offset(
        self, client: TestClient, sample_member_payload: dict
    ) -> None:
        """The `offset` query parameter skips the first N items."""
        # Create 5 members
        for i in range(5):
            payload = {**sample_member_payload, "email": f"user{i}@example.com"}
            client.post("/api/v1/members", json=payload)

        response = client.get("/api/v1/members", params={"offset": 3})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # 5 total − 3 skipped = 2

    def test_list_members_pagination_limit_and_offset(
        self, client: TestClient, sample_member_payload: dict
    ) -> None:
        """Combined limit + offset returns the correct slice."""
        # Create 5 members
        for i in range(5):
            payload = {**sample_member_payload, "email": f"user{i}@example.com"}
            client.post("/api/v1/members", json=payload)

        response = client.get(
            "/api/v1/members", params={"limit": 2, "offset": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_members_includes_created(
        self, client: TestClient, created_member: dict
    ) -> None:
        """A created member appears in the list."""
        response = client.get("/api/v1/members")
        members = response.json()
        ids = [m["id"] for m in members]
        assert created_member["id"] in ids


# ---------------------------------------------------------------------------
# 2. POST /api/v1/members — create
# ---------------------------------------------------------------------------

class TestCreateMember:
    """Tests for POST /api/v1/members."""

    def test_create_member_returns_201(
        self, client: TestClient, sample_member_payload: dict
    ) -> None:
        """Successful creation returns HTTP 201."""
        response = client.post("/api/v1/members", json=sample_member_payload)
        assert response.status_code == 201

    def test_create_member_response_body(
        self, client: TestClient, sample_member_payload: dict
    ) -> None:
        """Response contains the submitted fields plus an id."""
        response = client.post("/api/v1/members", json=sample_member_payload)
        body = response.json()
        assert body["name"] == sample_member_payload["name"]
        assert body["email"] == sample_member_payload["email"]
        assert body["role"] == sample_member_payload["role"]
        assert "id" in body

    def test_create_member_persists(
        self, client: TestClient, sample_member_payload: dict
    ) -> None:
        """A created member can be retrieved afterwards."""
        create_resp = client.post("/api/v1/members", json=sample_member_payload)
        member_id = create_resp.json()["id"]

        get_resp = client.get(f"/api/v1/members/{member_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["email"] == sample_member_payload["email"]

    def test_create_member_missing_name_returns_422(
        self, client: TestClient
    ) -> None:
        """Omitting the required `name` field triggers a 422."""
        payload = {"email": "no-name@example.com", "role": "member"}
        response = client.post("/api/v1/members", json=payload)
        assert response.status_code == 422

    def test_create_member_missing_email_returns_422(
        self, client: TestClient
    ) -> None:
        """Omitting the required `email` field triggers a 422."""
        payload = {"name": "No Email", "role": "member"}
        response = client.post("/api/v1/members", json=payload)
        assert response.status_code == 422

    def test_create_member_invalid_email_returns_422(
        self, client: TestClient
    ) -> None:
        """A malformed email address triggers a 422."""
        payload = {
            "name": "Bad Email",
            "email": "not-an-email",
            "role": "member",
        }
        response = client.post("/api/v1/members", json=payload)
        assert response.status_code == 422

    def test_create_member_duplicate_email_returns_409(
        self, client: TestClient, sample_member_payload: dict
    ) -> None:
        """Creating a member with a duplicate email returns 409 Conflict."""
        # First creation succeeds
        resp1 = client.post("/api/v1/members", json=sample_member_payload)
        assert resp1.status_code == 201

        # Second creation with same email fails
        resp2 = client.post("/api/v1/members", json=sample_member_payload)
        assert resp2.status_code == 409


# ---------------------------------------------------------------------------
# 3. GET /api/v1/members/{id} — retrieve
# ---------------------------------------------------------------------------

class TestGetMember:
    """Tests for GET /api/v1/members/{id}."""

    def test_get_member_returns_200(
        self, client: TestClient, created_member: dict
    ) -> None:
        """Retrieving an existing member returns 200."""
        response = client.get(f"/api/v1/members/{created_member['id']}")
        assert response.status_code == 200

    def test_get_member_response_body(
        self, client: TestClient, created_member: dict
    ) -> None:
        """Response body matches the created member."""
        response = client.get(f"/api/v1/members/{created_member['id']}")
        body = response.json()
        assert body["id"] == created_member["id"]
        assert body["name"] == created_member["name"]
        assert body["email"] == created_member["email"]
        assert body["role"] == created_member["role"]

    def test_get_member_not_found_returns_404(
        self, client: TestClient
    ) -> None:
        """Retrieving a non-existent member returns 404."""
        response = client.get("/api/v1/members/999999")
        assert response.status_code == 404

    def test_get_member_invalid_id_returns_422(
        self, client: TestClient
    ) -> None:
        """A non-integer id triggers a 422 validation error."""
        response = client.get("/api/v1/members/not-a-number")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 4. PUT /api/v1/members/{id} — update
# ---------------------------------------------------------------------------

class TestUpdateMember:
    """Tests for PUT /api/v1/members/{id}."""

    def test_update_member_returns_200(
        self, client: TestClient, created_member: dict
    ) -> None:
        """Successful update returns 200."""
        update_payload = {"name": "Alice Updated", "role": "admin"}
        response = client.put(
            f"/api/v1/members/{created_member['id']}", json=update_payload
        )
        assert response.status_code == 200

    def test_update_member_response_body(
        self, client: TestClient, created_member: dict
    ) -> None:
        """Response reflects the updated fields."""
        update_payload = {"name": "Alice Updated", "role": "admin"}
        response = client.put(
            f"/api/v1/members/{created_member['id']}", json=update_payload
        )
        body = response.json()
        assert body["id"] == created_member["id"]
        assert body["name"] == "Alice Updated"
        assert body["role"] == "admin"

    def test_update_member_persists(
        self, client: TestClient, created_member: dict
    ) -> None:
        """Updated values are persisted and visible on subsequent GET."""
        update_payload = {"name": "Alice Updated", "role": "admin"}
        client.put(
            f"/api/v1/members/{created_member['id']}", json=update_payload
        )

        get_resp = client.get(f"/api/v1/members/{created_member['id']}")
        body = get_resp.json()
        assert body["name"] == "Alice Updated"
        assert body["role"] == "admin"

    def test_update_member_not_found_returns_404(
        self, client: TestClient
    ) -> None:
        """Updating a non-existent member returns 404."""
        response = client.put(
            "/api/v1/members/999999", json={"name": "Ghost"}
        )
        assert response.status_code == 404

    def test_update_member_invalid_id_returns_422(
        self, client: TestClient
    ) -> None:
        """A non-integer id triggers a 422 validation error."""
        response = client.put(
            "/api/v1/members/not-a-number", json={"name": "Bad ID"}
        )
        assert response.status_code == 422

    def test_update_member_empty_payload_returns_422(
        self, client: TestClient, created_member: dict
    ) -> None:
        """An empty update payload triggers a 422."""
        response = client.put(
            f"/api/v1/members/{created_member['id']}", json={}
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 5. DELETE /api/v1/members/{id} — delete
# ---------------------------------------------------------------------------

class TestDeleteMember:
    """Tests for DELETE /api/v1/members/{id}."""

    def test_delete_member_returns_204(
        self, client: TestClient, created_member: dict
    ) -> None:
        """Successful deletion returns 204 No Content."""
        response = client.delete(f"/api/v1/members/{created_member['id']}")
        assert response.status_code == 204

    def test_delete_member_removes_from_store(
        self, client: TestClient, created_member: dict
    ) -> None:
        """After deletion the member can no longer be retrieved."""
        client.delete(f"/api/v1/members/{created_member['id']}")

        get_resp = client.get(f"/api/v1/members/{created_member['id']}")
        assert get_resp.status_code == 404

    def test_delete_member_not_found_returns_404(
        self, client: TestClient
    ) -> None:
        """Deleting a non-existent member returns 404."""
        response = client.delete("/api/v1/members/999999")
        assert response.status_code == 404

    def test_delete_member_invalid_id_returns_422(
        self, client: TestClient
    ) -> None:
        """A non-integer id triggers a 422 validation error."""
        response = client.delete("/api/v1/members/not-a-number")
        assert response.status_code == 422

    def test_delete_member_idempotent_behaviour(
        self, client: TestClient, created_member: dict
    ) -> None:
        """Deleting the same member twice: first succeeds, second 404s."""
        resp1 = client.delete(f"/api/v1/members/{created_member['id']}")
        assert resp1.status_code == 204

        resp2 = client.delete(f"/api/v1/members/{created_member['id']}")
        assert resp2.status_code == 404
