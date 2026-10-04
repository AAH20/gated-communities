"""Tests for gated-communities models and schemas."""

import pytest
from pydantic import ValidationError


class TestCommunityModel:
    """Test community Pydantic model."""

    def test_valid_community(self):
        """Test valid community data."""
        from gated_communities.schemas import CommunityCreate
        
        data = {
            "name": "Test Community",
            "description": "Test description",
        }
        
        community = CommunityCreate(**data)
        assert community.name == "Test Community"

    def test_community_name_too_short(self):
        """Test community name validation."""
        from gated_communities.schemas import CommunityCreate
        
        with pytest.raises(ValidationError):
            CommunityCreate(name="")

    def test_community_name_too_long(self):
        """Test community name max length."""
        from gated_communities.schemas import CommunityCreate
        
        with pytest.raises(ValidationError):
            CommunityCreate(name="A" * 101)


class TestMemberModel:
    """Test member Pydantic model."""

    def test_valid_member(self):
        """Test valid member data."""
        from gated_communities.schemas import MemberCreate
        
        data = {
            "community_id": 1,
            "user_id": 1,
            "role": "member",
        }
        
        member = MemberCreate(**data)
        assert member.community_id == 1

    def test_member_role_validation(self):
        """Test member role validation."""
        from gated_communities.schemas import MemberCreate
        
        with pytest.raises(ValidationError):
            MemberCreate(community_id=1, user_id=1, role="invalid_role")


class TestPostModel:
    """Test post Pydantic model."""

    def test_valid_post(self):
        """Test valid post data."""
        from gated_communities.schemas import PostCreate
        
        data = {
            "community_id": 1,
            "author_id": 1,
            "title": "Test Post",
            "content": "Test content",
        }
        
        post = PostCreate(**data)
        assert post.title == "Test Post"

    def test_post_title_too_long(self):
        """Test post title max length."""
        from gated_communities.schemas import PostCreate
        
        with pytest.raises(ValidationError):
            PostCreate(
                community_id=1,
                author_id=1,
                title="A" * 501,
                content="Test",
            )


class TestTierModel:
    """Test tier Pydantic model."""

    def test_valid_tier(self):
        """Test valid tier data."""
        from gated_communities.schemas import TierCreate
        
        data = {
            "name": "Premium",
            "price": 99.99,
            "features": ["feature1", "feature2"],
        }
        
        tier = TierCreate(**data)
        assert tier.name == "Premium"

    def test_tier_price_validation(self):
        """Test tier price validation."""
        from gated_communities.schemas import TierCreate
        
        with pytest.raises(ValidationError):
            TierCreate(name="Test", price=-10)
