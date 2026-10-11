"""End-to-end integration tests for gated-communities.

The original file drove a fictional ``GatedCommunitiesClient`` (whose
``governance``/``reputation`` helpers do not exist). These tests instead walk
real, end-to-end HTTP flows across the mounted FastAPI routers:

1. Auth + tier management + websocket echo.
2. Community-scoped moderation queue and audit trail.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from gated_communities import models as m
from gated_communities.auth import get_current_user
from gated_communities.main import app

OWNER_UID = 515151


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    """Register a unique user over HTTP and return Bearer headers."""
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


@pytest.fixture
def seeded_community(db_session):
    """Seed a community with an OWNER membership (integer user id)."""
    community = m.Community(
        name=f"community-{uuid.uuid4().hex[:8]}",
        description="e2e seeded community",
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


# ---------------------------------------------------------------------------
# 1. Auth + tiers + websocket
# ---------------------------------------------------------------------------


def test_auth_tier_and_websocket_flow(client: TestClient) -> None:
    """register → login → create tier → list tiers → websocket echo."""
    username = f"e2e-{uuid.uuid4().hex[:8]}"
    registered = client.post(
        "/auth/register",
        json={
            "username": username,
            "password": "testpass123",
            "email": f"{username}@example.com",
        },
    )
    assert registered.status_code == 201
    assert registered.json()["id"]

    login = client.post(
        "/auth/login", json={"username": username, "password": "testpass123"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # --- create tier ---
    tier = client.post(
        "/tiers",
        json={"name": "E2E Tier", "level": "silver", "description": "e2e"},
    )
    assert tier.status_code == 201
    assert tier.json()["name"] == "E2E Tier"

    # --- list tiers ---
    tiers = client.get("/tiers")
    assert tiers.status_code == 200
    assert any(t["name"] == "E2E Tier" for t in tiers.json())

    # --- websocket echo (authenticated) ---
    with client.websocket_connect(
        f"/ws?community_id=e2e-community&token={token}"
    ) as websocket:
        websocket.send_text("hello")
        assert websocket.receive_text() == "Message: hello"

    # --- authenticated identity ---
    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["username"] == username


# ---------------------------------------------------------------------------
# 2. Community moderation + audit
# ---------------------------------------------------------------------------


def test_community_moderation_and_audit_flow(
    client: TestClient, as_owner, seeded_community
) -> None:
    """Seed a community → file a moderation item → read the queue → audit."""
    community_id = seeded_community.id

    # --- create a moderation item ---
    created = client.post(
        "/moderation/items",
        json={
            "community_id": community_id,
            "reporter_id": 1,
            "target_type": "post",
            "target_id": 1,
            "reason": "spam",
        },
    )
    assert created.status_code == 201
    item = created.json()
    assert item["community_id"] == community_id
    assert item["status"] == "pending"

    # --- read the queue (moderator/owner required) ---
    queue = client.get("/moderation/queue")
    assert queue.status_code == 200
    assert any(row["id"] == item["id"] for row in queue.json())

    # --- write and read the audit trail ---
    audit = client.post(
        "/audit",
        json={
            "community_id": community_id,
            "user_id": 1,
            "action": "moderation_item_created",
            "details": "{}",
        },
    )
    assert audit.status_code == 201
    assert audit.json()["action"] == "moderation_item_created"

    listed = client.get("/audit")
    assert listed.status_code == 200
    assert any(
        entry["action"] == "moderation_item_created" for entry in listed.json()
    )
