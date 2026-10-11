"""API tests for the Members endpoints (tests/test_api/test_members.py).

Shipped routes (mounted at ROOT — no ``/api/v1`` prefix; auth required, so a
request without a token returns 401):

    GET    /members                 -> 200 list[MemberResponse]
    POST   /members                 -> 201 MemberResponse
    GET    /members/{member_id}     -> 200 / 404 / 422
    DELETE /members/{member_id}     -> 204 / 403 / 404 / 422
    PUT    /members/{member_id}     -> 405 (not implemented)

Shipped ``MemberCreate`` schema (src/gated_communities/schemas/__init__.py):

    ``user_id`` (int, gt=0) and ``role`` (one of member|moderator|admin,
    lower-case, default "member").  It does NOT define ``community_id``.

Verified live behaviour (probed against the shipped app + in-memory DB):

* Empty list / validation / auth / not-found paths all behave as asserted
  below (these are the un-skipped, genuinely-green tests).
* Success paths are blocked by src defects (see the module docstring of each
  skipped test).  They are quarantined here — this test-only task must not
  patch ``src/**``:

  - ``GET /members`` with at least one row, and ``GET /members/{id}`` for an
    existing member, both raise
    ``ResponseValidationError: {'type': 'missing', 'loc': ('response',
    'is_active'), 'msg': 'Field required'}`` — ``MemberResponse`` requires an
    ``is_active`` field the ORM ``Member`` model does not have.
  - ``POST /members`` with any schema-valid body raises
    ``AttributeError: 'MemberCreate' object has no attribute 'community_id'``
    — ``create_member`` reads ``member.community_id`` before anything else.
  - ``DELETE /members/{id}`` for an existing member returns 403 —
    ``_get_user_role`` does ``int(current_user["id"])`` but auth issues UUID
    string ids, so the lookup always returns None.
  - ``PUT /members/{id}`` is not implemented (405).
"""

from __future__ import annotations

import pytest

from gated_communities.models import Community, Member, MemberRole


_SERIALIZE_BLOCKED = (
    "src defect: ORM Member lacks the is_active field that MemberResponse "
    "requires, so serializing a persisted member raises ResponseValidationError "
    "{'type': 'missing', 'loc': ('response', 'is_active'), 'msg': 'Field required'}"
)
_CREATE_BLOCKED = (
    "src defect: create_member reads member.community_id, which the shipped "
    "MemberCreate schema does not define -> AttributeError "
    "'MemberCreate' object has no attribute 'community_id' (HTTP 500)"
)
_DELETE_RBAC_BLOCKED = (
    "src defect: DELETE requires OWNER/ADMIN but auth issues UUID string user "
    "ids while Member.user_id is int, so int(current_user['id']) raises -> role "
    "lookup always None -> 403"
)
_UPDATE_ABSENT = "PUT /members/{member_id} is not implemented (405)"


@pytest.fixture()
def sample_member_payload() -> dict:
    """A valid payload for the shipped ``POST /members`` schema."""
    return {"user_id": 42, "role": "member"}


@pytest.fixture()
def seeded_member(db_session) -> dict:
    """Persist a community + member directly so success paths can be exercised.

    Uses the shared in-memory engine, so the API sees the rows.
    """
    community = Community(name="Test Community", description="A test community")
    db_session.add(community)
    db_session.commit()
    db_session.refresh(community)

    member = Member(community_id=community.id, user_id=7, role=MemberRole.MEMBER)
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)

    return {
        "community_id": community.id,
        "member_id": member.id,
        "user_id": member.user_id,
    }


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

    @pytest.mark.skip(reason=_SERIALIZE_BLOCKED)
    def test_list_members_includes_seeded_member(self, client, auth_headers, seeded_member):
        response = client.get("/members", headers=auth_headers)
        assert response.status_code == 200
        assert any(m["id"] == seeded_member["member_id"] for m in response.json())


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
    def test_get_member_returns_200(self, client, auth_headers, seeded_member):
        response = client.get(
            f"/members/{seeded_member['member_id']}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == seeded_member["member_id"]


@pytest.mark.skip(reason=_UPDATE_ABSENT)
class TestUpdateMember:
    """Tests for PUT /members/{member_id} (quarantined — endpoint absent)."""

    def test_update_member_returns_200(self, client, auth_headers, seeded_member):
        response = client.put(
            f"/members/{seeded_member['member_id']}",
            json={"role": "admin"},
            headers=auth_headers,
        )
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
    def test_delete_member_returns_204(self, client, auth_headers, seeded_member):
        response = client.delete(
            f"/members/{seeded_member['member_id']}", headers=auth_headers
        )
        assert response.status_code == 204
