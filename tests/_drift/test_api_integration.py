"""API integration tests for all endpoints."""

import pytest


class TestHealthEndpoints:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_readiness_check(self, client):
        resp = client.get("/ready")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ready"}

    def test_liveness_check(self, client):
        resp = client.get("/live")
        assert resp.status_code == 200
        assert resp.json() == {"status": "alive"}


class TestCommunityEndpoints:
    def test_create_community(self, client, sample_community, auth_headers):
        resp = client.post("/communities", json=sample_community, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Community"
        assert data["tier_id"] == "free"
        assert "id" in data

    def test_list_communities_empty(self, client, auth_headers):
        resp = client.get("/communities", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_communities_with_data(self, client, sample_community, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        resp = client.get("/communities", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Community"

    def test_get_community(self, client, sample_community, auth_headers):
        create_resp = client.post("/communities", json=sample_community, headers=auth_headers)
        community_id = create_resp.json()["id"]
        resp = client.get(f"/communities/{community_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Community"

    def test_get_community_not_found(self, client, auth_headers):
        resp = client.get("/communities/9999", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_community(self, client, sample_community, auth_headers):
        create_resp = client.post("/communities", json=sample_community, headers=auth_headers)
        community_id = create_resp.json()["id"]
        resp = client.delete(f"/communities/{community_id}", headers=auth_headers)
        assert resp.status_code == 204
        resp = client.get(f"/communities/{community_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_community_not_found(self, client, auth_headers):
        resp = client.delete("/communities/9999", headers=auth_headers)
        assert resp.status_code == 404

    def test_list_communities_filter_private(self, client, auth_headers):
        client.post("/communities", json={"name": "Public", "is_private": False}, headers=auth_headers)
        client.post("/communities", json={"name": "Private", "is_private": True}, headers=auth_headers)
        resp = client.get("/communities", params={"include_private": False}, headers=auth_headers)
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Public"

    def test_list_communities_filter_tier(self, client, auth_headers):
        client.post("/communities", json={"name": "Free", "tier_id": "free"}, headers=auth_headers)
        client.post("/communities", json={"name": "Pro", "tier_id": "pro"}, headers=auth_headers)
        resp = client.get("/communities", params={"tier_id": "pro"}, headers=auth_headers)
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Pro"

    def test_create_community_validation_error(self, client, auth_headers):
        resp = client.post("/communities", json={"name": ""}, headers=auth_headers)
        assert resp.status_code == 422


class TestMemberEndpoints:
    def test_create_member(self, client, sample_community, sample_member, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        resp = client.post("/members", json=sample_member)
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"

    def test_create_member_invalid_email(self, client, sample_community, sample_member, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        sample_member["email"] = "not-an-email"
        resp = client.post("/members", json=sample_member)
        assert resp.status_code == 422

    def test_create_member_community_not_found(self, client, sample_member):
        resp = client.post("/members", json=sample_member)
        assert resp.status_code == 404

    def test_list_members(self, client, sample_community, sample_member, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        client.post("/members", json=sample_member)
        resp = client.get("/members")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    def test_list_members_filter_by_community(self, client, sample_community, sample_member, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        client.post("/members", json=sample_member)
        resp = client.get("/members", params={"community_id": 1})
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        resp = client.get("/members", params={"community_id": 999})
        assert len(resp.json()) == 0

    def test_get_member(self, client, sample_community, sample_member, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        create_resp = client.post("/members", json=sample_member)
        member_id = create_resp.json()["id"]
        resp = client.get(f"/members/{member_id}")
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    def test_get_member_not_found(self, client):
        resp = client.get("/members/9999")
        assert resp.status_code == 404

    def test_delete_member(self, client, sample_community, sample_member, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        create_resp = client.post("/members", json=sample_member)
        member_id = create_resp.json()["id"]
        resp = client.delete(f"/members/{member_id}")
        assert resp.status_code == 204

    def test_delete_member_not_found(self, client):
        resp = client.delete("/members/9999")
        assert resp.status_code == 404


class TestModerationEndpoints:
    def test_create_moderation_item(self, client):
        resp = client.post("/moderation/items", json={
            "type": "spam",
            "author": "user1",
            "reason": "Spam content",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["type"] == "spam"
        assert data["status"] == "pending"

    def test_get_moderation_queue(self, client):
        client.post("/moderation/items", json={"type": "spam", "author": "u1"})
        client.post("/moderation/items", json={"type": "abuse", "author": "u2"})
        resp = client.get("/moderation/queue")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_moderation_queue_empty(self, client):
        resp = client.get("/moderation/queue")
        assert resp.status_code == 200
        assert resp.json() == []


class TestSearchEndpoint:
    def test_search_communities(self, client, sample_community, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        resp = client.get("/search", params={"q": "Test", "type": "communities"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["communities"]) == 1

    def test_search_members(self, client, sample_community, sample_member, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        client.post("/members", json=sample_member)
        resp = client.get("/search", params={"q": "Test", "type": "members"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["members"]) == 1

    def test_search_all(self, client, sample_community, sample_member, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        client.post("/members", json=sample_member)
        resp = client.get("/search", params={"q": "Test", "type": "all"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["communities"]) == 1
        assert len(data["members"]) == 1

    def test_search_no_results(self, client):
        resp = client.get("/search", params={"q": "nonexistent"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["communities"] == []
        assert data["members"] == []

    def test_search_missing_query(self, client):
        resp = client.get("/search")
        assert resp.status_code == 422


class TestAuditEndpoints:
    def test_create_audit_log(self, client):
        resp = client.post("/audit", json={
            "user_id": "user1",
            "action": "login",
            "resource_type": "session",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["action"] == "login"
        assert data["user_id"] == "user1"

    def test_list_audit_logs(self, client):
        client.post("/audit", json={"user_id": "u1", "action": "login"})
        client.post("/audit", json={"user_id": "u2", "action": "logout"})
        resp = client.get("/audit")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_audit_logs_filter_user(self, client):
        client.post("/audit", json={"user_id": "u1", "action": "login"})
        client.post("/audit", json={"user_id": "u2", "action": "logout"})
        resp = client.get("/audit", params={"user_id": "u1"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_audit_logs_filter_resource_type(self, client):
        client.post("/audit", json={"user_id": "u1", "action": "login", "resource_type": "session"})
        client.post("/audit", json={"user_id": "u2", "action": "update", "resource_type": "profile"})
        resp = client.get("/audit", params={"resource_type": "session"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_audit_log(self, client):
        create_resp = client.post("/audit", json={"user_id": "u1", "action": "login"})
        log_id = create_resp.json()["id"]
        resp = client.get(f"/audit/{log_id}")
        assert resp.status_code == 200
        assert resp.json()["action"] == "login"

    def test_get_audit_log_not_found(self, client):
        resp = client.get("/audit/9999")
        assert resp.status_code == 404


class TestExportEndpoints:
    def test_export_members_json(self, client, sample_community, sample_member, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        client.post("/members", json=sample_member)
        resp = client.get("/export/members", params={"format": "json"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert len(data["members"]) == 1

    def test_export_members_csv(self, client, sample_community, sample_member, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        client.post("/members", json=sample_member)
        resp = client.get("/export/members", params={"format": "csv"})
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "Content-Disposition" in resp.headers

    def test_export_analytics(self, client, sample_community, sample_member, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        client.post("/members", json=sample_member)
        resp = client.get("/export/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_communities"] == 1
        assert data["total_members"] == 1


class TestBulkEndpoints:
    def test_bulk_update_members(self, client, sample_community, sample_member, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        m1 = client.post("/members", json=sample_member).json()
        m2 = client.post("/members", json={**sample_member, "email": "other@example.com"}).json()
        resp = client.post("/bulk/members/update", json={
            "member_ids": [m1["id"], m2["id"]],
            "action": "update",
            "role": "admin",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success_count"] == 2
        assert data["failure_count"] == 0

    def test_bulk_remove_members(self, client, sample_community, sample_member, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        m1 = client.post("/members", json=sample_member).json()
        resp = client.post("/bulk/members/update", json={
            "member_ids": [m1["id"]],
            "action": "remove",
        })
        assert resp.status_code == 200
        assert resp.json()["success_count"] == 1

    def test_bulk_update_with_failures(self, client, sample_community, sample_member, auth_headers):
        client.post("/communities", json=sample_community, headers=auth_headers)
        m1 = client.post("/members", json=sample_member).json()
        resp = client.post("/bulk/members/update", json={
            "member_ids": [m1["id"], 9999],
            "action": "update",
            "role": "admin",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success_count"] == 1
        assert data["failure_count"] == 1

    def test_bulk_update_invalid_action(self, client):
        resp = client.post("/bulk/members/update", json={
            "member_ids": [1],
            "action": "invalid",
        })
        assert resp.status_code == 422


class TestWebSocketEndpoint:
    @pytest.mark.asyncio
    async def test_websocket_connection(self, client):
        with client.websocket_connect("/ws?community_id=test1") as ws:
            ws.send_text("hello")
            data = ws.receive_text()
            assert "hello" in data

    @pytest.mark.asyncio
    async def test_websocket_broadcast(self, client):
        with client.websocket_connect("/ws?community_id=test2") as ws1:
            with client.websocket_connect("/ws?community_id=test2") as ws2:
                ws1.send_text("broadcast")
                data = ws2.receive_text()
                assert "broadcast" in data
