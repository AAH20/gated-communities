"""End-to-end integration tests combining API, DB, and domain logic."""

import pytest
from gated_communities.community import Community, CommunityConfig, CommunityVisibility
from gated_communities.member import Member, MemberRole, MemberStatus
from gated_communities.gate import Gate, GateRule, GateType
from gated_communities.access import AccessController, AccessDecision
from gated_communities.events import EventBus, CommunityEvent, CommunityEventType


class TestEndToEndCommunityLifecycle:
    def test_full_community_lifecycle(self, client, db_session, auth_headers):
        # Create community via API
        resp = client.post("/communities", json={
            "name": "E2E Community",
            "description": "End to end test",
            "is_private": False,
            "tier_id": "pro",
            "capacity": 500,
        }, headers=auth_headers)
        assert resp.status_code == 201
        community_id = resp.json()["id"]

        # Add members via API
        for i in range(3):
            resp = client.post("/members", json={
                "email": f"user{i}@example.com",
                "name": f"User {i}",
                "role": "member",
                "community_id": community_id,
            })
            assert resp.status_code == 201

        # Verify members in DB
        resp = client.get("/members", params={"community_id": community_id})
        assert len(resp.json()) == 3

        # Search for community
        resp = client.get("/search", params={"q": "E2E", "type": "communities"})
        assert len(resp.json()["communities"]) == 1

        # Export members
        resp = client.get("/export/members", params={"format": "json"})
        assert resp.json()["count"] == 3

        # Bulk update
        member_ids = [m["id"] for m in resp.json()["members"]]
        resp = client.post("/bulk/members/update", json={
            "member_ids": member_ids,
            "action": "update",
            "role": "moderator",
        })
        assert resp.json()["success_count"] == 3

        # Verify update
        resp = client.get(f"/members/{member_ids[0]}")
        assert resp.json()["role"] == "moderator"

        # Delete community
        resp = client.delete(f"/communities/{community_id}", headers=auth_headers)
        assert resp.status_code == 204

        # Verify cascade delete
        resp = client.get("/members", params={"community_id": community_id})
        assert len(resp.json()) == 0


class TestEndToEndAccessControl:
    def test_access_control_flow(self, client, db_session, auth_headers):
        # Create community
        client.post("/communities", json={"name": "Gated", "tier_id": "pro"}, headers=auth_headers)

        # Create member
        member_resp = client.post("/members", json={
            "email": "gated@example.com",
            "name": "Gated User",
            "community_id": 1,
        })
        assert member_resp.status_code == 201

        # Set up access control with domain gate
        config = CommunityConfig(
            name="Gated",
            require_approval=False,
        )
        community = Community(config=config)
        rule = GateRule(
            gate_type=GateType.DOMAIN_WHITELIST,
            name="corp-domain",
            config={"allowed_domains": ["corp.com"]},
        )
        gate = Gate(rules=[rule])
        controller = AccessController()

        # Test access denied for wrong domain
        result = controller.evaluate_access(
            "user1", community, gate, {"email": "user@gmail.com"}
        )
        assert result.decision == AccessDecision.DENIED

        # Test access granted for correct domain
        result = controller.evaluate_access(
            "user2", community, gate, {"email": "user@corp.com"}
        )
        assert result.decision == AccessDecision.GRANTED

        # Log audit events
        client.post("/audit", json={
            "user_id": "user1",
            "action": "access_denied",
            "resource_type": "community",
            "resource_id": "1",
        })
        client.post("/audit", json={
            "user_id": "user2",
            "action": "access_granted",
            "resource_type": "community",
            "resource_id": "1",
        })

        # Verify audit logs
        resp = client.get("/audit", params={"resource_type": "community"})
        assert len(resp.json()) == 2


class TestEndToEndEventDriven:
    def test_event_driven_workflow(self, client, db_session, auth_headers):
        bus = EventBus()
        events_received = []

        def track_event(e):
            events_received.append(e.event_type.value)

        bus.subscribe(CommunityEventType.COMMUNITY_CREATED, track_event)
        bus.subscribe(CommunityEventType.MEMBER_JOINED, track_event)
        bus.subscribe(CommunityEventType.ACCESS_GRANTED, track_event)

        # Create community
        resp = client.post("/communities", json={"name": "Event Community"}, headers=auth_headers)
        community_id = resp.json()["id"]
        bus.publish(CommunityEvent(
            event_type=CommunityEventType.COMMUNITY_CREATED,
            community_id=str(community_id),
        ))

        # Add member
        client.post("/members", json={
            "email": "event@example.com",
            "name": "Event User",
            "community_id": community_id,
        })
        bus.publish(CommunityEvent(
            event_type=CommunityEventType.MEMBER_JOINED,
            community_id=str(community_id),
            user_id="event@example.com",
        ))

        # Grant access
        bus.publish(CommunityEvent(
            event_type=CommunityEventType.ACCESS_GRANTED,
            community_id=str(community_id),
            user_id="event@example.com",
        ))

        assert len(events_received) == 3
        assert "community_created" in events_received
        assert "member_joined" in events_received
        assert "access_granted" in events_received


class TestEndToEndModerationWorkflow:
    def test_moderation_workflow(self, client, db_session, auth_headers):
        # Create community and members
        client.post("/communities", json={"name": "Mod Community"}, headers=auth_headers)
        m1 = client.post("/members", json={
            "email": "mod@example.com",
            "name": "Mod",
            "role": "moderator",
            "community_id": 1,
        }).json()
        m2 = client.post("/members", json={
            "email": "bad@example.com",
            "name": "Bad Actor",
            "role": "member",
            "community_id": 1,
        }).json()

        # Submit moderation item
        resp = client.post("/moderation/items", json={
            "type": "spam",
            "author": m2["name"],
            "reason": "Posted spam links",
        })
        assert resp.status_code == 201

        # Check queue
        resp = client.get("/moderation/queue")
        assert len(resp.json()) == 1

        # Log audit
        client.post("/audit", json={
            "user_id": m1["email"],
            "action": "moderation_action",
            "resource_type": "moderation_item",
        })

        # Verify audit
        resp = client.get("/audit", params={"user_id": m1["email"]})
        assert len(resp.json()) == 1


class TestEndToEndSearchAndExport:
    def test_search_and_export_integration(self, client, db_session, auth_headers):
        # Create multiple communities
        for i in range(3):
            client.post("/communities", json={
                "name": f"Community {i}",
                "tier_id": "pro" if i > 0 else "free",
            }, headers=auth_headers)

        # Add members to each
        for i in range(1, 4):
            client.post("/members", json={
                "email": f"user{i}@example.com",
                "name": f"User {i}",
                "community_id": i,
            })

        # Search
        resp = client.get("/search", params={"q": "Community", "type": "all"})
        data = resp.json()
        assert len(data["communities"]) == 3
        assert len(data["members"]) == 0  # Members don't match "Community"

        # Export analytics
        resp = client.get("/export/analytics")
        assert resp.json()["total_communities"] == 3
        assert resp.json()["total_members"] == 3

        # Export CSV
        resp = client.get("/export/members", params={"format": "csv"})
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
