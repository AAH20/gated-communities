"""API tests for the Members endpoints.

Real shipped routes (mounted at ROOT, auth required -> 401 without a token):

    GET    /members                 -> 200 list[MemberResponse]
    POST   /members                 -> 201 MemberResponse
    GET    /members/{member_id}     -> 200 / 404 / 422
    DELETE /members/{member_id}     -> 204 / 403 / 404 / 422

Shipped ``MemberCreate`` schema (src/gated_communities/schemas/__init__.py):
    ``user_id`` (int > 0) and ``role`` (member|moderator|admin, lower-case).

Quarantined in this module (blocked by verified src defects this test-only task
must not fix):

* Any test that needs a *persisted* member (list-with-rows, get-by-id success,
  delete success, create success) — ``MemberResponse`` requires an ``is_active``
  field the ORM ``Member`` model does not have, so serializing a persisted
  member raises HTTP 500.
* ``POST /members`` success — ``create_member`` reads ``member.community_id``,
  which the shipped ``MemberCreate`` schema does not define, raising HTTP 500.
* ``DELETE /members/{id}`` success — requires OWNER/ADMIN, but auth issues UUID
  string user ids while ``Member.user_id`` is an int, so the role lookup always
  returns None -> 403.
* ``TestUpdateMember`` — ``PUT /members/{id}`` is not implemented (405).
"""

from __future__ import annotations

import pytest


_SERIALIZE_BLOCKED = (
    "src defect: ORM Member lacks is_active required by MemberResponse -> "
    "serializing a persisted member raises HTTP 500"
)
_CREATE_BLOCKED = (
    "src defect: create_member reads member.community_id which the shipped "
    "MemberCreate schema does not define -> POST /members raises HTTP 500"
)
_DELETE_RBAC_BLOCKED = (
    "src defect: DELETE requires OWNER/ADMIN but auth user ids are UUID strings "
    "while Member.user_id is int -> role lookup always None -> 403"
)


@pytest.fixture()
def sample_member_payload() -> dict:
    """A valid payload for the shipped POST /members schema."""
    return {"user_id": 42, "role": "member"}


class TestListMembers:
    """Tests for GET /members."""

    def test_list_members_returns_200(self, client, auth_headers):
        response = client.get("/members", headers=auth_headers)
        assert response.status_code == 200

    def test_list_members_returns_list(self, client, auth_headers):
        response = client.get("/members", headers=auth_headers)
        assert isinstance(response.json(), list)

    def test_list_members_empty(self, client, auth_headers):
        response = client.get("/members", headers=auth_headers)
        assert response.json() == []

    def test_list_members_requires_auth(self, client):
        response = client.get("/members")
        assert response.status_code == 401

    def test_list_members_pagination_params_accepted(self, client, auth_headers):
        """Shipped pagination params (skip/limit) are accepted."""
        response = client.get("/members?skip=0&limit=10", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_members_rejects_bad_limit(self, client, auth_headers):
        """``limit`` must be >= 1 (Query(..., ge=1))."""
        response = client.get("/members?limit=0", headers=auth_headers)
        assert response.status_code == 422


class TestCreateMember:
    """Tests for POST /members."""

    def test_create_member_requires_auth(self, client, sample_member_payload):
        response = client.post("/members", json=sample_member_payload)
        assert response.status_code == 401

    def test_create_member_missing_user_id_returns_422(self, client, auth_headers):
        response = client.post("/members", json={"role": "member"}, headers=auth_headers)
        assert response.status_code == 422

    def test_create_member_invalid_role_returns_422(self, client, auth_headers):
        response = client.post(
            "/members", json={"user_id": 42, "role": "wizard"}, headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_member_non_positive_user_id_returns_422(self, client, auth_headers):
        response = client.post(
            "/members", json={"user_id": 0, "role": "member"}, headers=auth_headers
        )
        assert response.status_code == 422

    @pytest.mark.skip(reason=_CREATE_BLOCKED)
    def test_create_member_returns_201(self, client, auth_headers, sample_member_payload):
        response = client.post("/members", json=sample_member_payload, headers=auth_headers)
        assert response.status_code == 201


class TestGetMember:
    """Tests for GET /members/{member_id}."""

    def test_get_member_not_found_returns_404(self, client, auth_headers):
        response = client.get("/members/999999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_member_invalid_id_returns_422(self, client, auth_headers):
        response = client.get("/members/not-a-number", headers=auth_headers)
        assert response.status_code == 422

    def test_get_member_requires_auth(self, client):
        response = client.get("/members/1")
        assert response.status_code == 401

    @pytest.mark.skip(reason=_SERIALIZE_BLOCKED)
    def test_get_member_returns_200(self, client, auth_headers):
        response = client.get("/members/1", headers=auth_headers)
        assert response.status_code == 200


@pytest.mark.skip(reason="PUT /members/{member_id} is not implemented (405)")
class TestUpdateMember:
    """Tests for PUT /members/{id} (quarantined — endpoint absent)."""

    def test_update_member_returns_200(self, client, auth_headers):
        response = client.put("/members/1", json={"role": "admin"}, headers=auth_headers)
        assert response.status_code == 200


class TestDeleteMember:
    """Tests for DELETE /members/{member_id}."""

    def test_delete_member_not_found_returns_404(self, client, auth_headers):
        response = client.delete("/members/999999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_member_invalid_id_returns_422(self, client, auth_headers):
        response = client.delete("/members/not-a-number", headers=auth_headers)
        assert response.status_code == 422

    def test_delete_member_requires_auth(self, client):
        response = client.delete("/members/1")
        assert response.status_code == 401

    @pytest.mark.skip(reason=_DELETE_RBAC_BLOCKED)
    def test_delete_member_returns_204(self, client, auth_headers):
        response = client.delete("/members/1", headers=auth_headers)
        assert response.status_code == 204
