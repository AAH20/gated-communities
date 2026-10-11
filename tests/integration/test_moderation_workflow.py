"""Integration tests for the moderation workflow in gated-communities.

The original file exercised a fictional in-memory ``ModerationService`` /
``ModerationQueue`` API (``create_item``, ``enqueue``, ``process_next``,
``ModerationAnalytics`` ...) which does not exist -- ``gated_communities.moderation``
exposes only ``ModerationQueue.add``/``get_pending``. These tests instead drive the
real moderation router (``api/moderation.py``) over HTTP:

* ``POST /moderation/items`` (authenticated) creates a pending item.
* ``GET  /moderation/queue`` requires a moderator/owner membership and returns
  the pending items.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from gated_communities import models as m
from gated_communities.auth import get_current_user
from gated_communities.main import app

OWNER_UID = 828282


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
        description="moderation workflow community",
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


def _item_payload(community_id: int, reason: str = "spam") -> dict:
    return {
        "community_id": community_id,
        "reporter_id": 1,
        "target_type": "post",
        "target_id": 1,
        "reason": reason,
    }


class TestModerationItemLifecycle:
    """Tests for creating and reading moderation items."""

    def test_create_moderation_item(
        self, client: TestClient, auth_headers: dict, seeded_community
    ) -> None:
        response = client.post(
            "/moderation/items",
            json=_item_payload(seeded_community.id),
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["community_id"] == seeded_community.id
        assert data["reason"] == "spam"
        assert data["status"] == "pending"

    def test_create_moderation_item_validation(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        response = client.post("/moderation/items", json={}, headers=auth_headers)
        assert response.status_code == 422

    def test_create_moderation_item_requires_auth(
        self, client: TestClient, seeded_community
    ) -> None:
        response = client.post(
            "/moderation/items", json=_item_payload(seeded_community.id)
        )
        assert response.status_code == 401


class TestModerationQueueFlow:
    """Tests for the moderation queue access and listing."""

    def test_moderation_queue_requires_auth(self, client: TestClient) -> None:
        assert client.get("/moderation/queue").status_code == 401

    def test_moderation_queue_requires_moderator(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        response = client.get("/moderation/queue", headers=auth_headers)
        assert response.status_code == 403

    def test_moderation_queue_lists_pending_items(
        self, client: TestClient, as_owner, seeded_community
    ) -> None:
        created = client.post(
            "/moderation/items", json=_item_payload(seeded_community.id)
        )
        assert created.status_code == 201
        item_id = created.json()["id"]

        queue = client.get("/moderation/queue")
        assert queue.status_code == 200
        ids = [row["id"] for row in queue.json()]
        assert item_id in ids
