"""End-to-end integration tests for gated-communities.

Covers the three core flows:
1. Full community lifecycle (community → member → post → comment → event → moderate)
2. Governance (community → policy → enforce → analytics)
3. Reputation (member → update reputation → score → access check)
"""

from __future__ import annotations

import pytest

from gated_communities import GatedCommunitiesClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> GatedCommunitiesClient:
    """Provide a fresh client instance for each test."""
    return GatedCommunitiesClient()


@pytest.fixture
def community(client: GatedCommunitiesClient) -> dict:
    """Create a community and return its data."""
    return client.communities.create(
        name="Test Community",
        description="Integration test community",
        visibility="private",
    )


@pytest.fixture
def member(client: GatedCommunitiesClient, community: dict) -> dict:
    """Add a member to the community and return the membership record."""
    return client.members.add(
        community_id=community["id"],
        user_id="user-001",
        role="member",
    )


# ---------------------------------------------------------------------------
# 1. Full community flow
# ---------------------------------------------------------------------------


def test_full_community_flow(client: GatedCommunitiesClient) -> None:
    """create community → add member → create post → add comment → create event → moderate."""
    # --- create community ---
    community = client.communities.create(
        name="E2E Community",
        description="Full lifecycle test",
        visibility="private",
    )
    assert community["id"]
    assert community["name"] == "E2E Community"
    assert community["member_count"] == 0

    # --- add member ---
    membership = client.members.add(
        community_id=community["id"],
        user_id="user-001",
        role="member",
    )
    assert membership["community_id"] == community["id"]
    assert membership["user_id"] == "user-001"
    assert membership["role"] == "member"

    # --- create post ---
    post = client.posts.create(
        community_id=community["id"],
        author_id="user-001",
        title="Hello World",
        content="First post in the community",
    )
    assert post["id"]
    assert post["community_id"] == community["id"]
    assert post["author_id"] == "user-001"
    assert post["title"] == "Hello World"

    # --- add comment ---
    comment = client.comments.create(
        post_id=post["id"],
        author_id="user-001",
        content="Nice post!",
    )
    assert comment["id"]
    assert comment["post_id"] == post["id"]
    assert comment["author_id"] == "user-001"
    assert comment["content"] == "Nice post!"

    # --- create event ---
    event = client.events.create(
        community_id=community["id"],
        title="Community Meetup",
        description="Monthly gathering",
        start_time="2026-11-01T18:00:00Z",
        end_time="2026-11-01T20:00:00Z",
    )
    assert event["id"]
    assert event["community_id"] == community["id"]
    assert event["title"] == "Community Meetup"

    # --- moderate (remove the comment) ---
    moderation = client.moderation.remove_content(
        content_type="comment",
        content_id=comment["id"],
        reason="spam",
    )
    assert moderation["action"] == "removed"
    assert moderation["content_id"] == comment["id"]
    assert moderation["reason"] == "spam"

    # Verify the comment is no longer visible
    remaining = client.comments.list(post_id=post["id"])
    assert all(c["id"] != comment["id"] for c in remaining)


# ---------------------------------------------------------------------------
# 2. Governance flow
# ---------------------------------------------------------------------------


def test_governance_flow(client: GatedCommunitiesClient) -> None:
    """create community → create policy → enforce → get analytics."""
    # --- create community ---
    community = client.communities.create(
        name="Governance Community",
        description="Governance test",
        visibility="private",
    )
    assert community["id"]

    # --- create policy ---
    policy = client.governance.create_policy(
        community_id=community["id"],
        name="No Spam",
        description="Prohibit spam content",
        rules=[{"type": "keyword_block", "values": ["buy now", "free money"]}],
        action="flag",
    )
    assert policy["id"]
    assert policy["community_id"] == community["id"]
    assert policy["name"] == "No Spam"
    assert policy["action"] == "flag"

    # --- enforce (submit content that violates the policy) ---
    enforcement = client.governance.enforce(
        policy_id=policy["id"],
        content_type="post",
        content="Click here for free money now!",
    )
    assert enforcement["policy_id"] == policy["id"]
    assert enforcement["action_taken"] == "flag"
    assert enforcement["matched_rules"]  # at least one rule matched

    # --- get analytics ---
    analytics = client.governance.get_analytics(community_id=community["id"])
    assert analytics["community_id"] == community["id"]
    assert analytics["total_policies"] >= 1
    assert analytics["total_enforcements"] >= 1
    assert analytics["flagged_content"] >= 1


# ---------------------------------------------------------------------------
# 3. Reputation flow
# ---------------------------------------------------------------------------


def test_reputation_flow(client: GatedCommunitiesClient) -> None:
    """create member → update reputation → get score → check access."""
    # --- create community (needed for membership context) ---
    community = client.communities.create(
        name="Reputation Community",
        description="Reputation test",
        visibility="private",
    )
    assert community["id"]

    # --- create member ---
    membership = client.members.add(
        community_id=community["id"],
        user_id="user-002",
        role="member",
    )
    assert membership["user_id"] == "user-002"

    # --- update reputation ---
    reputation_update = client.reputation.update(
        community_id=community["id"],
        user_id="user-002",
        delta=25,
        reason="helpful contribution",
    )
    assert reputation_update["user_id"] == "user-002"
    assert reputation_update["delta"] == 25

    # --- get score ---
    score = client.reputation.get_score(
        community_id=community["id"],
        user_id="user-002",
    )
    assert score["user_id"] == "user-002"
    assert score["score"] == 25
    assert score["tier"] in {"bronze", "silver", "gold", "platinum"}

    # --- check access (score-based gating) ---
    access = client.reputation.check_access(
        community_id=community["id"],
        user_id="user-002",
        required_score=10,
    )
    assert access["user_id"] == "user-002"
    assert access["has_access"] is True
    assert access["score"] >= 10

    # --- check access denied for higher threshold ---
    access_denied = client.reputation.check_access(
        community_id=community["id"],
        user_id="user-002",
        required_score=100,
    )
    assert access_denied["has_access"] is False
    assert access_denied["score"] < 100
