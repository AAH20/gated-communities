"""Authorization bypass tests for gated-communities."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gated_communities.main import app
from gated_communities.auth import register_user, create_access_token


class TestAuthorizationBypass:
    """Test that authorization cannot be bypassed."""

    @pytest.fixture
    def client(self):
        with TestClient(app) as c:
            yield c

    def test_unauthenticated_cannot_create_community(self, client):
        """Test that unauthenticated users cannot create communities."""
        resp = client.post(
            "/communities",
            json={
                "name": "Test Community",
                "description": "Test",
                "is_private": False,
                "tier_id": "free",
                "capacity": 100
            }
        )
        assert resp.status_code in (401, 403), (
            "Unauthenticated user created a community"
        )

    def test_unauthenticated_cannot_delete_community(self, client):
        """Test that unauthenticated users cannot delete communities."""
        resp = client.delete("/communities/1")
        assert resp.status_code in (401, 403), (
            "Unauthenticated user deleted a community"
        )

    def test_unauthenticated_cannot_access_moderation(self, client):
        """Test that unauthenticated users cannot access moderation."""
        resp = client.get("/moderation/queue")
        assert resp.status_code in (401, 403), (
            "Unauthenticated user accessed moderation"
        )

    def test_unauthenticated_cannot_access_audit(self, client):
        """Test that unauthenticated users cannot access audit logs."""
        resp = client.get("/audit")
        assert resp.status_code in (401, 403), (
            "Unauthenticated user accessed audit logs"
        )

    def test_unauthenticated_cannot_access_export(self, client):
        """Test that unauthenticated users cannot access export."""
        resp = client.get("/export/members")
        assert resp.status_code in (401, 403), (
            "Unauthenticated user accessed export"
        )

    def test_token_with_invalid_user_rejected(self, client):
        """Test that tokens for non-existent users are rejected."""
        # Create a token for a user that doesn't exist
        token = create_access_token("nonexistent_user_12345")
        resp = client.get(
            "/communities",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Should be rejected because user doesn't exist
        assert resp.status_code in (401, 403), (
            "Token for non-existent user was accepted"
        )

    def test_revoked_token_rejected(self, client):
        """Test that revoked tokens are rejected."""
        from gated_communities.auth import revoke_token, _users

        register_user("revoketest", "revoke@example.com", "testpass123")
        # Get the user's actual ID (UUID) to create a valid token
        user = _users["revoketest"]
        token = create_access_token(user["id"])

        # Revoke the token
        revoke_token(token)

        resp = client.get(
            "/communities",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 401, "Revoked token was accepted"
