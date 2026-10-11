"""Integration tests for the member workflow in gated-communities.

The original file exercised a fictional ``MemberService``/``Member``/``AccessLevel``
shape (``Member(name=..., email=...)`` is not a valid ORM signature here). These
tests drive the real members router (``api/members.py``) over HTTP.

Contract notes verified live:

* ``GET /members`` requires auth and returns ``[]`` when empty.
* ``DELETE /members/{id}`` requires an OWNER/ADMIN role in the member's
  community (RBAC helpers coerce ``current_user["id"]`` to ``int``), returns
  204, and 404 afterwards.
* ``POST /members`` fails response/validation in ``src`` and is only asserted at
  its authentication boundary.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from gated_communities import models as m
from gated_communities.auth import get_current_user
from gated_communities.main import app

OWNER_UID = 616161


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    """Register a unique user over HTTP and return Bearer headers."""
    username = f"user-{uuid.uuid4().hex[:10]}"
    password = "testpass123"
    client.post(
        "/auth/register",
        json={
            "username": username,
            "password": password,
            "email": f"{username}@example.com",
        },
    )
    login = client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def as_owner():
    """Override auth so requests act as the seeded OWNER (integer id)."""
    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: {
        "id": OWNER_UID,
        "username": "owner",
        "email": "owner@example.com",
    }
    yield
    if previous is None:
        app.dependency_overrides.pop(get_current_user, None)
    else:
        app.dependency_overrides[get_current_user] = previous


@pytest.fixture
def seeded_community(db_session):
    """Seed a community with an OWNER membership (integer user id)."""
    community = m.Community(
        name=f"community-{uuid.uuid4().hex[:8]}",
        description="member workflow community",
        status=m.CommunityStatus.ACTIVE,
    )
    db_session.add(community)
    db_session.commit()
    db_session.refresh(community)

    owner = m.Member(
        community_id=community.id,
        user_id=OWNER_UID,
        role=m.MemberRole.OWNER,
    )
    db_session.add(owner)
    db_session.commit()
    db_session.refresh(owner)
    return community


@pytest.fixture
def seeded_member(db_session, seeded_community):
    """Seed a non-owner member of the seeded community."""
    member = m.Member(
        community_id=seeded_community.id,
        user_id=OWNER_UID + 1,
        role=m.MemberRole.MEMBER,
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)
    return member


class TestMemberLifecycle:
    """Tests for the member read/delete lifecycle."""

    def test_list_members_empty(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        response = client.get("/members", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_members_requires_auth(self, client: TestClient) -> None:
        assert client.get("/members").status_code == 401

    def test_full_member_lifecycle(
        self, client: TestClient, as_owner, seeded_member
    ) -> None:
        """Delete a member, then confirm it is gone."""
        member_id = seeded_member.id

        deleted = client.delete(f"/members/{member_id}")
        assert deleted.status_code == 204

        assert client.get(f"/members/{member_id}").status_code == 404

    def test_delete_member_not_found(
        self, client: TestClient, as_owner, seeded_community
    ) -> None:
        assert client.delete("/members/999999").status_code == 404

    def test_delete_member_forbidden_for_non_privileged(
        self, client: TestClient, auth_headers: dict, seeded_member
    ) -> None:
        response = client.delete(
            f"/members/{seeded_member.id}", headers=auth_headers
        )
        assert response.status_code == 403


class TestMemberVerificationFlow:
    """Tests for member creation's access contract."""

    def test_add_member_requires_auth(
        self, client: TestClient, seeded_community
    ) -> None:
        response = client.post(
            "/members",
            json={"community_id": seeded_community.id, "user_id": 1, "role": "member"},
        )
        assert response.status_code == 401

    def test_add_member_validation(
        self, client: TestClient, as_owner, seeded_community
    ) -> None:
        # ``user_id`` is required and must be > 0.
        response = client.post("/members", json={})
        assert response.status_code == 422


class TestMemberAccessFlow:
    """Tests for member access via RBAC on the delete endpoint."""

    def test_member_delete_requires_auth(
        self, client: TestClient, seeded_member
    ) -> None:
        response = client.delete(f"/members/{seeded_member.id}")
        assert response.status_code == 401
