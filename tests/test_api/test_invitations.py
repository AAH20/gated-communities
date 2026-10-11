"""API tests for the Invitations endpoints.

Real shipped routes (mounted at ROOT):

    GET  /invitations  -> 200 {"items": [...], "total", "page", "page_size", "pages"}
    POST /invitations  -> 201 InvitationResponse

The router (src/gated_communities/api/invitations.py) is backed by an in-memory
mock store seeded on import.  ``InvitationCreate`` requires ``community_id``
(must exist in the mock map: comm-001..comm-005) and a valid ``email``; ``role``
is optional (default "member").

Endpoint coverage note:

* The shipped router exposes no ``/invitations/{id}`` route, so
  ``TestGetInvitation`` / ``TestUpdateInvitation`` / ``TestDeleteInvitation``
  assert the real contract (fail closed: 404/405) rather than success.
"""

import pytest


@pytest.fixture
def sample_invitation_payload():
    return {
        "community_id": "comm-001",
        "email": "invitee@example.com",
        "role": "member",
        "message": "Join our community!",
    }


@pytest.fixture
def created_invitation(client, sample_invitation_payload):
    response = client.post("/invitations", json=sample_invitation_payload)
    assert response.status_code == 201, response.text
    return response.json()


class TestListInvitations:
    """Tests for GET /invitations."""

    def test_list_invitations_returns_200(self, client):
        assert client.get("/invitations").status_code == 200

    def test_list_invitations_envelope(self, client):
        data = client.get("/invitations").json()
        assert {"items", "total", "page", "page_size", "pages"}.issubset(data)
        assert isinstance(data["items"], list)

    def test_list_invitations_seeded(self, client):
        assert client.get("/invitations").json()["total"] >= 1

    def test_list_invitations_page_size_caps(self, client):
        response = client.get("/invitations", params={"page_size": 2})
        assert response.status_code == 200
        assert len(response.json()["items"]) <= 2

    def test_list_invitations_filter_by_status(self, client):
        response = client.get("/invitations", params={"status": "pending"})
        assert response.status_code == 200
        for inv in response.json()["items"]:
            assert inv["status"] == "pending"

    def test_list_invitations_filter_by_community(self, client):
        response = client.get("/invitations", params={"community_id": "comm-001"})
        assert response.status_code == 200
        for inv in response.json()["items"]:
            assert inv["community_id"] == "comm-001"

    def test_list_invitations_invalid_status(self, client):
        assert client.get("/invitations", params={"status": "bogus"}).status_code == 422


class TestCreateInvitation:
    """Tests for POST /invitations."""

    def test_create_invitation_returns_201(self, client, sample_invitation_payload):
        response = client.post("/invitations", json=sample_invitation_payload)
        assert response.status_code == 201

    def test_create_invitation_response_body(self, client, sample_invitation_payload):
        data = client.post("/invitations", json=sample_invitation_payload).json()
        assert data["email"] == sample_invitation_payload["email"]
        assert data["role"] == sample_invitation_payload["role"]
        assert data["community_id"] == sample_invitation_payload["community_id"]
        assert data["status"] == "pending"
        assert "id" in data

    def test_create_invitation_persists(self, client, created_invitation):
        items = client.get("/invitations", params={"page_size": 100}).json()["items"]
        ids = [inv["id"] for inv in items]
        assert created_invitation["id"] in ids

    def test_create_invitation_missing_email_returns_422(self, client):
        response = client.post("/invitations", json={"community_id": "comm-001"})
        assert response.status_code == 422

    def test_create_invitation_invalid_email_returns_422(self, client):
        response = client.post("/invitations", json={"community_id": "comm-001", "email": "not-an-email"})
        assert response.status_code == 422

    def test_create_invitation_unknown_community_returns_404(self, client):
        response = client.post("/invitations", json={"community_id": "comm-999", "email": "a@b.com"})
        assert response.status_code == 404

    def test_create_invitation_empty_body_returns_422(self, client):
        assert client.post("/invitations", json={}).status_code == 422

    def test_create_invitation_invalid_expires_in_days(self, client):
        response = client.post(
            "/invitations",
            json={"community_id": "comm-001", "email": "a@b.com", "expires_in_days": 0},
        )
        assert response.status_code == 422


class TestGetInvitation:
    """GET /invitations/{id} is not implemented in the shipped router.

    The router exposes only ``GET ''`` and ``POST ''``, so the single-invitation
    path is unrouted and must fail closed (404/405) rather than appear to
    succeed.
    """

    def test_get_invitation_route_absent(self, client, created_invitation):
        response = client.get(f"/invitations/{created_invitation['id']}")
        assert response.status_code in (404, 405)

    def test_get_invitation_unknown_id_route_absent(self, client):
        response = client.get("/invitations/does-not-exist")
        assert response.status_code in (404, 405)


class TestUpdateInvitation:
    """PUT /invitations/{id} is not implemented — must fail closed (404/405)."""

    def test_update_invitation_route_absent(self, client, created_invitation):
        response = client.put(f"/invitations/{created_invitation['id']}", json={"role": "admin"})
        assert response.status_code in (404, 405)


class TestDeleteInvitation:
    """DELETE /invitations/{id} is not implemented — must fail closed (404/405)."""

    def test_delete_invitation_route_absent(self, client, created_invitation):
        response = client.delete(f"/invitations/{created_invitation['id']}")
        assert response.status_code in (404, 405)
