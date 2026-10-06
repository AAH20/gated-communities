"""Unit tests for domain models."""

import pytest
from gated_communities.community import Community, CommunityConfig, CommunityVisibility
from gated_communities.member import Member, MemberRole, MemberStatus
from gated_communities.gate import Gate, GateRule, GateType
from gated_communities.access import AccessController, AccessRequest, AccessDecision
from gated_communities.events import EventBus, CommunityEvent, CommunityEventType


class TestCommunityModel:
    def test_create_community(self):
        config = CommunityConfig(name="Test", description="Desc")
        community = Community(config=config)
        assert community.config.name == "Test"
        assert community.member_count == 0
        assert community.is_active is True

    def test_can_join_active(self):
        config = CommunityConfig(name="Test")
        community = Community(config=config)
        assert community.can_join("user1") is True

    def test_can_join_inactive(self):
        config = CommunityConfig(name="Test")
        community = Community(config=config, is_active=False)
        assert community.can_join("user1") is False

    def test_can_join_full(self):
        config = CommunityConfig(name="Test", max_members=1)
        community = Community(config=config, member_count=1)
        assert community.can_join("user1") is False

    def test_to_dict(self):
        config = CommunityConfig(name="Test")
        community = Community(config=config)
        d = community.to_dict()
        assert d["name"] == "Test"
        assert d["visibility"] == "private"
        assert "id" in d
        assert "created_at" in d


class TestMemberModel:
    def test_create_member(self):
        member = Member(user_id="u1", community_id="c1")
        assert member.role == MemberRole.MEMBER
        assert member.status == MemberStatus.PENDING

    def test_can_moderate_owner(self):
        member = Member(user_id="u1", role=MemberRole.OWNER)
        assert member.can_moderate() is True

    def test_can_moderate_admin(self):
        member = Member(user_id="u1", role=MemberRole.ADMIN)
        assert member.can_moderate() is True

    def test_can_moderate_moderator(self):
        member = Member(user_id="u1", role=MemberRole.MODERATOR)
        assert member.can_moderate() is True

    def test_can_moderate_member(self):
        member = Member(user_id="u1", role=MemberRole.MEMBER)
        assert member.can_moderate() is False

    def test_can_invite_owner(self):
        member = Member(user_id="u1", role=MemberRole.OWNER)
        assert member.can_invite() is True

    def test_can_invite_admin(self):
        member = Member(user_id="u1", role=MemberRole.ADMIN)
        assert member.can_invite() is True

    def test_can_invite_member(self):
        member = Member(user_id="u1", role=MemberRole.MEMBER)
        assert member.can_invite() is False

    def test_to_dict(self):
        member = Member(user_id="u1", community_id="c1")
        d = member.to_dict()
        assert d["user_id"] == "u1"
        assert d["community_id"] == "c1"
        assert "id" in d


class TestGateModel:
    def test_gate_rule_evaluate_match(self):
        rule = GateRule(gate_type=GateType.INVITE_ONLY, name="invite")
        assert rule.evaluate({"has_invite": True}) is True

    def test_gate_rule_evaluate_no_match(self):
        rule = GateRule(gate_type=GateType.INVITE_ONLY, name="invite")
        assert rule.evaluate({"has_invite": False}) is False

    def test_gate_rule_inactive(self):
        rule = GateRule(gate_type=GateType.INVITE_ONLY, name="invite", is_active=False)
        assert rule.evaluate({"has_invite": False}) is True

    def test_gate_evaluate_all_pass(self):
        rule1 = GateRule(gate_type=GateType.INVITE_ONLY, name="r1")
        rule2 = GateRule(gate_type=GateType.PAYMENT, name="r2", config={"required_tier": "pro"})
        gate = Gate(rules=[rule1, rule2])
        passed, failed = gate.evaluate({"has_invite": True, "payment_tier": "pro"})
        assert passed is True
        assert failed == []

    def test_gate_evaluate_some_fail(self):
        rule1 = GateRule(gate_type=GateType.INVITE_ONLY, name="r1")
        rule2 = GateRule(gate_type=GateType.PAYMENT, name="r2", config={"required_tier": "pro"})
        gate = Gate(rules=[rule1, rule2])
        passed, failed = gate.evaluate({"has_invite": True, "payment_tier": "free"})
        assert passed is False
        assert "r2" in failed

    def test_domain_whitelist_gate(self):
        rule = GateRule(
            gate_type=GateType.DOMAIN_WHITELIST,
            name="domain",
            config={"allowed_domains": ["example.com"]},
        )
        assert rule.evaluate({"email": "user@example.com"}) is True
        assert rule.evaluate({"email": "user@other.com"}) is False

    def test_token_gate(self):
        rule = GateRule(
            gate_type=GateType.TOKEN_GATE,
            name="token",
            config={"required_token_address": "0x123"},
        )
        assert rule.evaluate({"token_addresses": ["0x123", "0x456"]}) is True
        assert rule.evaluate({"token_addresses": ["0x456"]}) is False

    def test_nft_gate(self):
        rule = GateRule(
            gate_type=GateType.NFT_GATE,
            name="nft",
            config={"required_collection": "CryptoPunks"},
        )
        assert rule.evaluate({"nft_collections": ["CryptoPunks"]}) is True
        assert rule.evaluate({"nft_collections": ["Other"]}) is False

    def test_custom_gate(self):
        rule = GateRule(
            gate_type=GateType.CUSTOM,
            name="custom",
            config={"custom_check": lambda ctx: ctx.get("score", 0) > 50},
        )
        assert rule.evaluate({"score": 75}) is True
        assert rule.evaluate({"score": 25}) is False


class TestAccessController:
    def test_grant_access_no_gates(self):
        controller = AccessController()
        config = CommunityConfig(name="Test", require_approval=False)
        community = Community(config=config)
        gate = Gate(rules=[])
        result = controller.evaluate_access("user1", community, gate)
        assert result.decision == AccessDecision.GRANTED

    def test_deny_when_community_inactive(self):
        controller = AccessController()
        config = CommunityConfig(name="Test")
        community = Community(config=config, is_active=False)
        gate = Gate(rules=[])
        result = controller.evaluate_access("user1", community, gate)
        assert result.decision == AccessDecision.DENIED

    def test_pending_when_approval_required(self):
        controller = AccessController()
        config = CommunityConfig(name="Test", require_approval=True)
        community = Community(config=config)
        gate = Gate(rules=[])
        result = controller.evaluate_access("user1", community, gate)
        assert result.decision == AccessDecision.PENDING

    def test_deny_when_gate_fails(self):
        controller = AccessController()
        config = CommunityConfig(name="Test", require_approval=False)
        community = Community(config=config)
        rule = GateRule(gate_type=GateType.INVITE_ONLY, name="invite")
        gate = Gate(rules=[rule])
        result = controller.evaluate_access("user1", community, gate, {"has_invite": False})
        assert result.decision == AccessDecision.DENIED

    def test_approve_request(self):
        controller = AccessController()
        config = CommunityConfig(name="Test", require_approval=True)
        community = Community(config=config)
        gate = Gate(rules=[])
        request = controller.evaluate_access("user1", community, gate)
        assert request.decision == AccessDecision.PENDING
        approved = controller.approve_request(request, "admin")
        assert approved.decision == AccessDecision.GRANTED
        assert approved.resolved_by == "admin"

    def test_deny_request(self):
        controller = AccessController()
        config = CommunityConfig(name="Test", require_approval=True)
        community = Community(config=config)
        gate = Gate(rules=[])
        request = controller.evaluate_access("user1", community, gate)
        denied = controller.deny_request(request, "admin", "Not qualified")
        assert denied.decision == AccessDecision.DENIED
        assert denied.reason == "Not qualified"


class TestEventBus:
    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []
        bus.subscribe(CommunityEventType.MEMBER_JOINED, lambda e: received.append(e))
        event = CommunityEvent(
            event_type=CommunityEventType.MEMBER_JOINED,
            community_id="c1",
            user_id="u1",
        )
        bus.publish(event)
        assert len(received) == 1
        assert received[0].user_id == "u1"

    def test_unsubscribe(self):
        bus = EventBus()
        received = []
        handler = lambda e: received.append(e)
        bus.subscribe(CommunityEventType.MEMBER_JOINED, handler)
        bus.unsubscribe(CommunityEventType.MEMBER_JOINED, handler)
        bus.publish(CommunityEvent(event_type=CommunityEventType.MEMBER_JOINED))
        assert len(received) == 0

    def test_get_history(self):
        bus = EventBus()
        bus.publish(CommunityEvent(event_type=CommunityEventType.COMMUNITY_CREATED, community_id="c1"))
        bus.publish(CommunityEvent(event_type=CommunityEventType.MEMBER_JOINED, community_id="c1"))
        bus.publish(CommunityEvent(event_type=CommunityEventType.MEMBER_JOINED, community_id="c2"))
        assert len(bus.get_history()) == 3
        assert len(bus.get_history(community_id="c1")) == 2
        assert len(bus.get_history(event_type=CommunityEventType.MEMBER_JOINED)) == 2

    def test_multiple_handlers(self):
        bus = EventBus()
        count = [0]
        bus.subscribe(CommunityEventType.MEMBER_JOINED, lambda e: count.__setitem__(0, count[0] + 1))
        bus.subscribe(CommunityEventType.MEMBER_JOINED, lambda e: count.__setitem__(0, count[0] + 1))
        bus.publish(CommunityEvent(event_type=CommunityEventType.MEMBER_JOINED))
        assert count[0] == 2
