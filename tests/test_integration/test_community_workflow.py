"""Integration tests for gated-communities workflows."""

import pytest
from fastapi.testclient import TestClient


class TestCommunityWorkflow:
    """Test complete community workflow."""

    def test_community_creation_to_member(self, client: TestClient):
        """Test community creation to member invitation."""
        # 1. Create community
        community_response = client.post("/api/communities", json={
            "name": "Test Community",
            "description": "Test description",
        })
        assert community_response.status_code == 201
        community_id = community_response.json()["id"]

        # 2. Add member
        member_response = client.post("/api/members", json={
            "community_id": community_id,
            "user_id": 1,
            "role": "member",
        })
        assert member_response.status_code == 201

        # 3. Create post
        post_response = client.post("/api/posts", json={
            "community_id": community_id,
            "author_id": 1,
            "title": "Test Post",
            "content": "Test content",
        })
        assert post_response.status_code == 201

    def test_tier_upgrade_flow(self, client: TestClient):
        """Test tier upgrade workflow."""
        # Create community
        community_response = client.post("/api/communities", json={
            "name": "Premium Community",
            "description": "Premium",
        })
        assert community_response.status_code == 201
        community_id = community_response.json()["id"]

        # Upgrade tier
        upgrade_response = client.post(f"/api/communities/{community_id}/upgrade", json={
            "tier": "premium",
        })
        assert upgrade_response.status_code == 200


class TestContentAccessWorkflow:
    """Test content access workflow."""

    def test_content_access_flow(self, client: TestClient):
        """Test content access based on tier."""
        # Create community
        community_response = client.post("/api/communities", json={
            "name": "Gated Community",
            "description": "Gated",
        })
        assert community_response.status_code == 201
        community_id = community_response.json()["id"]

        # Create gated content
        content_response = client.post("/api/content", json={
            "community_id": community_id,
            "title": "Gated Content",
            "content": "Premium content",
            "required_tier": "premium",
        })
        assert content_response.status_code == 201
