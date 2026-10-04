"""
Integration tests for gated-communities community workflows.

Tests cover:
1. Full community lifecycle (create → update → delete)
2. Community member flow (create → add member → remove member)
3. Community health flow (create → score health → flag unhealthy)
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from gated_communities import (
    Community,
    CommunityStatus,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def community_manager():
    """Provide a fresh CommunityManager instance for each test."""
    return CommunityManager()


@pytest.fixture
def sample_community_data():
    """Provide valid community creation payload."""
    return {
        "name": "Test Community",
        "description": "A test community for integration testing",
        "privacy": "private",
        "tags": ["test", "integration"],
    }


@pytest.fixture
def sample_member_data():
    """Provide valid member payload."""
    return {
        "user_id": "user-12345",
        "role": MembershipRole.MEMBER,
    }


@pytest.fixture
def created_community(community_manager, sample_community_data):
    """Create a community and return it for tests that need a pre-existing community."""
    community = community_manager.create_community(**sample_community_data)
    return community


@pytest.fixture
def community_with_member(community_manager, created_community, sample_member_data):
    """Create a community with one member already added."""
    member = community_manager.add_member(
        community_id=created_community.id, **sample_member_data
    )
    return created_community, member


# ---------------------------------------------------------------------------
# Test 1: Full Community Lifecycle
# ---------------------------------------------------------------------------


class TestFullCommunityLifecycle:
    """Test the complete lifecycle: create → update → delete."""

    def test_create_community(self, community_manager, sample_community_data):
        """Verify a community can be created with valid data."""
        community = community_manager.create_community(**sample_community_data)

        assert community is not None
        assert community.id is not None
        assert community.name == sample_community_data["name"]
        assert community.description == sample_community_data["description"]
        assert community.privacy == sample_community_data["privacy"]
        assert community.status == CommunityStatus.ACTIVE
        assert community.created_at is not None
        assert community.member_count == 0

    def test_update_community(self, community_manager, created_community):
        """Verify an existing community can be updated."""
        new_name = "Updated Test Community"
        new_description = "Updated description for the test community"

        updated = community_manager.update_community(
            community_id=created_community.id,
            name=new_name,
            description=new_description,
        )

        assert updated is not None
        assert updated.id == created_community.id
        assert updated.name == new_name
        assert updated.description == new_description
        assert updated.updated_at >= created_community.created_at

    def test_delete_community(self, community_manager, created_community):
        """Verify a community can be deleted and is no longer accessible."""
        community_id = created_community.id

        result = community_manager.delete_community(community_id=community_id)

        assert result is True

        # Verify the community no longer exists
        deleted = community_manager.get_community(community_id=community_id)
        assert deleted is None

    def test_full_lifecycle_sequence(self, community_manager, sample_community_data):
        """End-to-end: create → update → delete in a single flow."""
        # Step 1: Create
        community = community_manager.create_community(**sample_community_data)
        assert community.status == CommunityStatus.ACTIVE
        original_id = community.id

        # Step 2: Update
        updated = community_manager.update_community(
            community_id=original_id,
            name="Lifecycle Updated Community",
            tags=["lifecycle", "e2e"],
        )
        assert updated.name == "Lifecycle Updated Community"
        assert "lifecycle" in updated.tags

        # Step 3: Delete
        delete_result = community_manager.delete_community(community_id=original_id)
        assert delete_result is True

        # Verify deletion
        assert community_manager.get_community(community_id=original_id) is None


# ---------------------------------------------------------------------------
# Test 2: Community Member Flow
# ---------------------------------------------------------------------------


class TestCommunityMemberFlow:
    """Test member management: create community → add member → remove member."""

    def test_add_member_to_community(
        self, community_manager, created_community, sample_member_data
    ):
        """Verify a member can be added to an existing community."""
        member = community_manager.add_member(
            community_id=created_community.id, **sample_member_data
        )

        assert member is not None
        assert member.user_id == sample_member_data["user_id"]
        assert member.role == sample_member_data["role"]
        assert member.community_id == created_community.id
        assert member.joined_at is not None

        # Verify member count incremented
        community = community_manager.get_community(community_id=created_community.id)
        assert community.member_count == 1

    def test_remove_member_from_community(
        self, community_manager, community_with_member
    ):
        """Verify a member can be removed from a community."""
        community, member = community_with_member

        result = community_manager.remove_member(
            community_id=community.id, user_id=member.user_id
        )

        assert result is True

        # Verify member count decremented
        updated_community = community_manager.get_community(community_id=community.id)
        assert updated_community.member_count == 0

        # Verify member is no longer in the community
        members = community_manager.list_members(community_id=community.id)
        assert all(m.user_id != member.user_id for m in members)

    def test_member_flow_sequence(
        self, community_manager, sample_community_data, sample_member_data
    ):
        """End-to-end: create community → add member → remove member."""
        # Step 1: Create community
        community = community_manager.create_community(**sample_community_data)
        assert community.member_count == 0

        # Step 2: Add member
        member = community_manager.add_member(
            community_id=community.id, **sample_member_data
        )
        assert member.user_id == sample_member_data["user_id"]

        community = community_manager.get_community(community_id=community.id)
        assert community.member_count == 1

        # Step 3: Remove member
        remove_result = community_manager.remove_member(
            community_id=community.id, user_id=sample_member_data["user_id"]
        )
        assert remove_result is True

        community = community_manager.get_community(community_id=community.id)
        assert community.member_count == 0

    def test_add_multiple_members(self, community_manager, created_community):
        """Verify multiple members can be added to the same community."""
        user_ids = ["user-001", "user-002", "user-003"]

        for uid in user_ids:
            community_manager.add_member(
                community_id=created_community.id,
                user_id=uid,
                role=MembershipRole.MEMBER,
            )

        community = community_manager.get_community(community_id=created_community.id)
        assert community.member_count == 3

        members = community_manager.list_members(community_id=created_community.id)
        member_ids = {m.user_id for m in members}
        assert member_ids == set(user_ids)

    def test_remove_nonexistent_member_raises_error(
        self, community_manager, created_community
    ):
        """Verify removing a non-existent member raises an appropriate error."""
        with pytest.raises(ValueError, match="not a member"):
            community_manager.remove_member(
                community_id=created_community.id, user_id="nonexistent-user"
            )


# ---------------------------------------------------------------------------
# Test 3: Community Health Flow
# ---------------------------------------------------------------------------


class TestCommunityHealthFlow:
    """Test health scoring: create community → score health → flag unhealthy."""

    def test_score_community_health(self, community_manager, created_community):
        """Verify health can be scored for a community."""
        health = community_manager.score_health(community_id=created_community.id)

        assert health is not None
        assert health.community_id == created_community.id
        assert health.score is not None
        assert 0 <= health.score <= 100
        assert health.status is not None
        assert health.assessed_at is not None

    def test_healthy_community_status(self, community_manager, created_community):
        """Verify a new community with good metrics is flagged as healthy."""
        # Add some members to make it look active
        for i in range(5):
            community_manager.add_member(
                community_id=created_community.id,
                user_id=f"active-user-{i}",
                role=MembershipRole.MEMBER,
            )

        health = community_manager.score_health(community_id=created_community.id)

        assert health.status == HealthStatus.HEALTHY
        assert health.score >= 70

    def test_unhealthy_community_flagged(self, community_manager, sample_community_data):
        """Verify a community with poor metrics is flagged as unhealthy."""
        # Create a community but don't add any members (inactive)
        community = community_manager.create_community(**sample_community_data)

        health = community_manager.score_health(community_id=community.id)

        assert health.status == HealthStatus.UNHEALTHY
        assert health.score < 50

    def test_health_flow_sequence(self, community_manager, sample_community_data):
        """End-to-end: create community → score health → flag unhealthy."""
        # Step 1: Create community
        community = community_manager.create_community(**sample_community_data)
        assert community.status == CommunityStatus.ACTIVE

        # Step 2: Score health (new community with no members = unhealthy)
        health = community_manager.score_health(community_id=community.id)
        assert health is not None
        assert health.community_id == community.id

        # Step 3: Verify unhealthy flag
        assert health.status == HealthStatus.UNHEALTHY
        assert health.score < 50

        # Verify the community record reflects the health status
        community_record = community_manager.get_community(community_id=community.id)
        assert community_record.health_status == HealthStatus.UNHEALTHY

    def test_health_improves_with_activity(self, community_manager, sample_community_data):
        """Verify community health improves as activity increases."""
        community = community_manager.create_community(**sample_community_data)

        # Initial health score (no members)
        initial_health = community_manager.score_health(community_id=community.id)
        assert initial_health.status == HealthStatus.UNHEALTHY

        # Add members to improve health
        for i in range(10):
            community_manager.add_member(
                community_id=community.id,
                user_id=f"member-{i}",
                role=MembershipRole.MEMBER,
            )

        # Re-score health
        improved_health = community_manager.score_health(community_id=community.id)
        assert improved_health.score > initial_health.score
        assert improved_health.status == HealthStatus.HEALTHY

    def test_health_score_bounds(self, community_manager, created_community):
        """Verify health score always stays within valid bounds [0, 100]."""
        health = community_manager.score_health(community_id=created_community.id)

        assert 0 <= health.score <= 100
