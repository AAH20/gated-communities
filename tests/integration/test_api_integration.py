"""Integration tests for API endpoints.

These exercise the FastAPI app over HTTP via the ``client`` fixture. Paths are
the real, root-level routes served by ``gated_communities.main`` (there is no
``/api/v1`` prefix for communities/members/moderation/tiers/audit/export/bulk).

Privileged operations are covered by seeding a membership with an integer
``user_id`` and overriding the auth dependency, because the RBAC helpers coerce
``current_user["id"]`` to ``int`` while registered users carry UUID ids.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from gated_communities import models as m
from gated_communities.auth import get_current_user
from gated_communities.main import app

OWNER_UID = 424242


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_community(db_session):
    """Seed a community plus an OWNER membership (integer user id)."""
    community = m.Community(
        name=f"community-{uuid.uuid4().hex[:8]}",
        description="seeded for integration tests",
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
def auth_headers(client: TestClient) -> dict:
    """Register a unique user over HTTP and return Bearer headers.

    Shadowing the conftest fixture because its fixed ``testuser`` username
    collides (409) on the second test that requests it.
    """
    username = f"user-{uuid.uuid4().hex[:10]}"
    password = "testpass123"
    register = client.post(
        "/auth/register",
        json={
            "username": username,
            "password": password,
            "email": f"{username}@example.com",
        },
    )
    assert register.status_code == 201, register.text
    login = client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    assert login.status_code == 200, login.text
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


class TestHealthIntegration:
    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_readiness_check(self, client: TestClient) -> None:
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["ready"] is True

    def test_liveness_check(self, client: TestClient) -> None:
        response = client.get("/live")
        assert response.status_code == 200
        assert response.json() == {"alive": True}


class TestTiersIntegration:
    def test_create_tier(self, client: TestClient) -> None:
        response = client.post(
            "/tiers",
            json={
                "name": "Gold",
                "level": "gold",
                "description": "Gold tier",
                "benefits": ["priority_support"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Gold"
        assert data["level"] == "gold"

    def test_list_tiers(self, client: TestClient) -> None:
        response = client.get("/tiers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestModerationIntegration:
    def test_create_moderation_item(
        self, client: TestClient, auth_headers: dict, seeded_community
    ) -> None:
        response = client.post(
            "/moderation/items",
            json={
                "community_id": seeded_community.id,
                "reporter_id": 1,
                "target_type": "post",
                "target_id": 1,
                "reason": "spam",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["reason"] == "spam"
        assert data["status"] == "pending"

    def test_get_moderation_queue(
        self, client: TestClient, as_owner, seeded_community
    ) -> None:
        response = client.get("/moderation/queue")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_moderation_queue_requires_moderator(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        response = client.get("/moderation/queue", headers=auth_headers)
        assert response.status_code == 403


class TestWebSocketIntegration:
    def test_websocket_connection(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        token = auth_headers["Authorization"].split(" ", 1)[1]
        with client.websocket_connect(
            f"/ws?community_id=community123&token={token}"
        ) as websocket:
            websocket.send_text('{"type": "test"}')
            data = websocket.receive_text()
            assert data == 'Message: {"type": "test"}'


class TestExportIntegration:
    def test_export_members_requires_auth(self, client: TestClient) -> None:
        response = client.get("/export/members?format=csv")
        assert response.status_code == 401

    def test_export_members_forbidden_for_non_privileged(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        response = client.get("/export/members?format=csv", headers=auth_headers)
        assert response.status_code == 403


class TestSearchIntegration:
    def test_search_requires_auth(self, client: TestClient) -> None:
        response = client.get("/search?q=python")
        assert response.status_code == 401


class TestBulkOperationsIntegration:
    def test_bulk_member_update_forbidden_for_non_privileged(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        response = client.post(
            "/bulk/members/update",
            json={"member_ids": [1], "action": "update", "role": "moderator"},
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestAuditIntegration:
    def test_create_audit_log(
        self, client: TestClient, as_owner, seeded_community
    ) -> None:
        response = client.post(
            "/audit",
            json={
                "community_id": seeded_community.id,
                "user_id": 1,
                "action": "member_created",
                "details": "{}",
            },
        )
        assert response.status_code == 201
        assert response.json()["action"] == "member_created"

    def test_list_audit_logs(
        self, client: TestClient, as_owner, seeded_community
    ) -> None:
        response = client.get("/audit")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
