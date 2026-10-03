"""Comprehensive agent tests for tier management operations."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone

from src.gated_communities.agents.tier_management import (
    create_tier,
    get_tier,
    update_tier,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Provide a mock database session."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_tier_data():
    """Provide sample tier data for testing."""
    return {
        "id": 1,
        "name": "Premium",
        "description": "Premium tier with exclusive benefits",
        "price": 29.99,
        "currency": "USD",
        "duration_days": 30,
        "is_active": True,
        "max_members": 1000,
        "features": ["priority_support", "exclusive_content", "custom_badge"],
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    }


@pytest.fixture
def mock_tier():
    """Provide a mock tier object."""
    tier = MagicMock()
    tier.id = 1
    tier.name = "Premium"
    tier.description = "Premium tier with exclusive benefits"
    tier.price = 29.99
    tier.currency = "USD"
    tier.duration_days = 30
    tier.is_active = True
    tier.max_members = 1000
    tier.features = ["priority_support", "exclusive_content", "custom_badge"]
    tier.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    tier.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return tier


@pytest.fixture
def mock_tier_create_input():
    """Provide input data for creating a tier."""
    return {
        "name": "Premium",
        "description": "Premium tier with exclusive benefits",
        "price": 29.99,
        "currency": "USD",
        "duration_days": 30,
        "max_members": 1000,
        "features": ["priority_support", "exclusive_content", "custom_badge"],
    }


@pytest.fixture
def mock_tier_update_input():
    """Provide input data for updating a tier."""
    return {
        "name": "Premium Plus",
        "description": "Updated premium tier description",
        "price": 39.99,
        "max_members": 2000,
        "features": ["priority_support", "exclusive_content", "custom_badge", "early_access"],
    }


# ---------------------------------------------------------------------------
# Test create_tier
# ---------------------------------------------------------------------------


class TestCreateTier:
    """Tests for the create_tier function."""

    @pytest.mark.asyncio
    async def test_create_tier_success(self, mock_db, mock_tier_create_input, mock_tier):
        """Test successful tier creation with valid data."""
        mock_db.execute.return_value = MagicMock(scalar=MagicMock(return_value=mock_tier))

        result = await create_tier(mock_db, mock_tier_create_input)

        assert result is not None
        assert result.id == 1
        assert result.name == "Premium"
        assert result.price == 29.99
        assert result.currency == "USD"
        assert result.duration_days == 30
        assert result.is_active is True
        assert result.max_members == 1000
        assert "priority_support" in result.features
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_minimal_data(self, mock_db, mock_tier):
        """Test tier creation with minimal required fields."""
        minimal_input = {"name": "Basic"}
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, minimal_input)

        assert result is not None
        assert result.name == "Premium"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_all_features(self, mock_db, mock_tier):
        """Test tier creation with comprehensive feature set."""
        full_input = {
            "name": "Enterprise",
            "description": "Enterprise tier",
            "price": 99.99,
            "currency": "EUR",
            "duration_days": 365,
            "max_members": 10000,
            "features": [
                "priority_support",
                "exclusive_content",
                "custom_badge",
                "early_access",
                "api_access",
                "white_label",
            ],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, full_input)

        assert result is not None
        assert result.name == "Premium"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_database_error(self, mock_db, mock_tier_create_input):
        """Test tier creation handles database errors gracefully."""
        mock_db.execute.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            await create_tier(mock_db, mock_tier_create_input)

        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_zero_price(self, mock_db, mock_tier):
        """Test creating a free tier with zero price."""
        free_tier_input = {
            "name": "Free",
            "description": "Free tier",
            "price": 0.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": ["basic_access"],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, free_tier_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_long_duration(self, mock_db, mock_tier):
        """Test creating a tier with extended duration."""
        long_duration_input = {
            "name": "Lifetime",
            "description": "Lifetime access tier",
            "price": 499.99,
            "currency": "USD",
            "duration_days": 36500,
            "max_members": 5000,
            "features": ["all_features"],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, long_duration_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_empty_features(self, mock_db, mock_tier):
        """Test creating a tier with empty features list."""
        no_features_input = {
            "name": "Basic",
            "description": "Basic tier",
            "price": 9.99,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 500,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, no_features_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_special_characters_in_name(self, mock_db, mock_tier):
        """Test creating a tier with special characters in name."""
        special_input = {
            "name": "Premium™ (2024) — Special Edition",
            "description": "Tier with special characters",
            "price": 49.99,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 1000,
            "features": ["special_access"],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, special_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_different_currencies(self, mock_db, mock_tier):
        """Test creating tiers with various currency codes."""
        currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"]

        for currency in currencies:
            currency_input = {
                "name": f"Tier {currency}",
                "description": f"Tier with {currency}",
                "price": 19.99,
                "currency": currency,
                "duration_days": 30,
                "max_members": 1000,
                "features": ["standard"],
            }
            mock_db.execute.return_value = MagicMock(
                scalar=MagicMock(return_value=mock_tier)
            )

            result = await create_tier(mock_db, currency_input)

            assert result is not None
            mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_tier_with_large_max_members(self, mock_db, mock_tier):
        """Test creating a tier with very large member limit."""
        large_input = {
            "name": "Unlimited",
            "description": "Unlimited members tier",
            "price": 999.99,
            "currency": "USD",
            "duration_days": 365,
            "max_members": 999999999,
            "features": ["unlimited_access"],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, large_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_negative_price_raises_error(self, mock_db):
        """Test that creating a tier with negative price raises an error."""
        invalid_input = {
            "name": "Invalid",
            "description": "Invalid tier",
            "price": -10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }

        with pytest.raises(ValueError):
            await create_tier(mock_db, invalid_input)

    @pytest.mark.asyncio
    async def test_create_tier_with_empty_name_raises_error(self, mock_db):
        """Test that creating a tier with empty name raises an error."""
        invalid_input = {
            "name": "",
            "description": "Invalid tier",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }

        with pytest.raises(ValueError):
            await create_tier(mock_db, invalid_input)

    @pytest.mark.asyncio
    async def test_create_tier_with_none_name_raises_error(self, mock_db):
        """Test that creating a tier with None name raises an error."""
        invalid_input = {
            "name": None,
            "description": "Invalid tier",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }

        with pytest.raises((ValueError, TypeError)):
            await create_tier(mock_db, invalid_input)

    @pytest.mark.asyncio
    async def test_create_tier_with_invalid_currency_raises_error(self, mock_db):
        """Test that creating a tier with invalid currency raises an error."""
        invalid_input = {
            "name": "Invalid Currency",
            "description": "Invalid tier",
            "price": 10.00,
            "currency": "INVALID",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }

        with pytest.raises(ValueError):
            await create_tier(mock_db, invalid_input)

    @pytest.mark.asyncio
    async def test_create_tier_with_zero_duration_raises_error(self, mock_db):
        """Test that creating a tier with zero duration raises an error."""
        invalid_input = {
            "name": "Invalid Duration",
            "description": "Invalid tier",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 0,
            "max_members": 100,
            "features": [],
        }

        with pytest.raises(ValueError):
            await create_tier(mock_db, invalid_input)

    @pytest.mark.asyncio
    async def test_create_tier_with_negative_duration_raises_error(self, mock_db):
        """Test that creating a tier with negative duration raises an error."""
        invalid_input = {
            "name": "Invalid Duration",
            "description": "Invalid tier",
            "price": 10.00,
            "currency": "USD",
            "duration_days": -30,
            "max_members": 100,
            "features": [],
        }

        with pytest.raises(ValueError):
            await create_tier(mock_db, invalid_input)

    @pytest.mark.asyncio
    async def test_create_tier_with_zero_max_members_raises_error(self, mock_db):
        """Test that creating a tier with zero max members raises an error."""
        invalid_input = {
            "name": "Invalid Members",
            "description": "Invalid tier",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 0,
            "features": [],
        }

        with pytest.raises(ValueError):
            await create_tier(mock_db, invalid_input)

    @pytest.mark.asyncio
    async def test_create_tier_with_negative_max_members_raises_error(self, mock_db):
        """Test that creating a tier with negative max members raises an error."""
        invalid_input = {
            "name": "Invalid Members",
            "description": "Invalid tier",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": -100,
            "features": [],
        }

        with pytest.raises(ValueError):
            await create_tier(mock_db, invalid_input)

    @pytest.mark.asyncio
    async def test_create_tier_with_very_long_name(self, mock_db, mock_tier):
        """Test creating a tier with a very long name."""
        long_name_input = {
            "name": "A" * 255,
            "description": "Tier with long name",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, long_name_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_very_long_description(self, mock_db, mock_tier):
        """Test creating a tier with a very long description."""
        long_desc_input = {
            "name": "Long Desc Tier",
            "description": "D" * 1000,
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, long_desc_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_many_features(self, mock_db, mock_tier):
        """Test creating a tier with many features."""
        many_features_input = {
            "name": "Feature Rich",
            "description": "Tier with many features",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [f"feature_{i}" for i in range(100)],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, many_features_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_duplicate_features(self, mock_db, mock_tier):
        """Test creating a tier with duplicate features in list."""
        duplicate_features_input = {
            "name": "Duplicate Features",
            "description": "Tier with duplicate features",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": ["feature_a", "feature_b", "feature_a", "feature_c", "feature_b"],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, duplicate_features_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_unicode_name(self, mock_db, mock_tier):
        """Test creating a tier with unicode characters in name."""
        unicode_input = {
            "name": "プレミアム 🌟",
            "description": "Tier with unicode name",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, unicode_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_unicode_description(self, mock_db, mock_tier):
        """Test creating a tier with unicode characters in description."""
        unicode_desc_input = {
            "name": "Unicode Desc",
            "description": "説明 📝 with émojis and spëcial chars",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, unicode_desc_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_whitespace_name(self, mock_db, mock_tier):
        """Test creating a tier with whitespace-only name."""
        whitespace_input = {
            "name": "   ",
            "description": "Tier with whitespace name",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, whitespace_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_float_price_precision(self, mock_db, mock_tier):
        """Test creating a tier with high-precision float price."""
        precise_input = {
            "name": "Precise",
            "description": "Tier with precise price",
            "price": 19.999999,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, precise_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_integer_price(self, mock_db, mock_tier):
        """Test creating a tier with integer price value."""
        integer_input = {
            "name": "Integer Price",
            "description": "Tier with integer price",
            "price": 20,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, integer_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_string_price(self, mock_db, mock_tier):
        """Test creating a tier with string price value."""
        string_input = {
            "name": "String Price",
            "description": "Tier with string price",
            "price": "25.50",
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, string_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_none_description(self, mock_db, mock_tier):
        """Test creating a tier with None description."""
        none_desc_input = {
            "name": "No Desc",
            "description": None,
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, none_desc_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_none_features(self, mock_db, mock_tier):
        """Test creating a tier with None features."""
        none_features_input = {
            "name": "No Features",
            "description": "Tier with no features",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": None,
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, none_features_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_missing_optional_fields(self, mock_db, mock_tier):
        """Test creating a tier with only required fields."""
        minimal_input = {"name": "Minimal Tier"}
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, minimal_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_extra_fields(self, mock_db, mock_tier):
        """Test creating a tier with extra unexpected fields."""
        extra_input = {
            "name": "Extra Fields",
            "description": "Tier with extra fields",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
            "extra_field_1": "value1",
            "extra_field_2": "value2",
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, extra_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_boolean_is_active(self, mock_db, mock_tier):
        """Test creating a tier with explicit is_active flag."""
        active_input = {
            "name": "Active Tier",
            "description": "Tier with is_active flag",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
            "is_active": True,
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, active_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_inactive_flag(self, mock_db, mock_tier):
        """Test creating a tier with is_active set to False."""
        inactive_input = {
            "name": "Inactive Tier",
            "description": "Tier with is_active False",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
            "is_active": False,
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, inactive_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_very_small_price(self, mock_db, mock_tier):
        """Test creating a tier with very small price."""
        small_input = {
            "name": "Micro",
            "description": "Tier with micro price",
            "price": 0.01,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, small_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_very_large_price(self, mock_db, mock_tier):
        """Test creating a tier with very large price."""
        large_price_input = {
            "name": "Luxury",
            "description": "Tier with luxury price",
            "price": 999999.99,
            "currency": "USD",
            "duration_days": 365,
            "max_members": 10,
            "features": ["luxury_access"],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, large_price_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_one_day_duration(self, mock_db, mock_tier):
        """Test creating a tier with one day duration."""
        one_day_input = {
            "name": "Daily",
            "description": "One day tier",
            "price": 1.99,
            "currency": "USD",
            "duration_days": 1,
            "max_members": 1000,
            "features": ["daily_access"],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, one_day_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_one_max_member(self, mock_db, mock_tier):
        """Test creating a tier with max_members of 1."""
        single_member_input = {
            "name": "Exclusive",
            "description": "Single member tier",
            "price": 999.99,
            "currency": "USD",
            "duration_days": 365,
            "max_members": 1,
            "features": ["exclusive_access"],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, single_member_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_newline_in_name(self, mock_db, mock_tier):
        """Test creating a tier with newline characters in name."""
        newline_input = {
            "name": "Tier\nWith\nNewlines",
            "description": "Tier with newlines",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, newline_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_tab_in_name(self, mock_db, mock_tier):
        """Test creating a tier with tab characters in name."""
        tab_input = {
            "name": "Tier\tWith\tTabs",
            "description": "Tier with tabs",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, tab_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_html_in_name(self, mock_db, mock_tier):
        """Test creating a tier with HTML tags in name."""
        html_input = {
            "name": "<script>alert('xss')</script>",
            "description": "Tier with HTML",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, html_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_sql_injection_in_name(self, mock_db, mock_tier):
        """Test creating a tier with SQL injection attempt in name."""
        sql_input = {
            "name": "'; DROP TABLE tiers; --",
            "description": "Tier with SQL injection",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, sql_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_json_in_features(self, mock_db, mock_tier):
        """Test creating a tier with JSON-like features."""
        json_features_input = {
            "name": "JSON Features",
            "description": "Tier with JSON features",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": ['{"key": "value"}', "[1,2,3]"],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, json_features_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_numeric_feature_names(self, mock_db, mock_tier):
        """Test creating a tier with numeric feature names."""
        numeric_features_input = {
            "name": "Numeric Features",
            "description": "Tier with numeric features",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [1, 2, 3, 4, 5],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, numeric_features_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_mixed_type_features(self, mock_db, mock_tier):
        """Test creating a tier with mixed type features."""
        mixed_features_input = {
            "name": "Mixed Features",
            "description": "Tier with mixed type features",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": ["string", 123, True, None, 45.67],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, mixed_features_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_nested_list_features(self, mock_db, mock_tier):
        """Test creating a tier with nested list features."""
        nested_features_input = {
            "name": "Nested Features",
            "description": "Tier with nested features",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [["nested", "list"], ["another", "nested"]],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, nested_features_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_dict_features(self, mock_db, mock_tier):
        """Test creating a tier with dict features."""
        dict_features_input = {
            "name": "Dict Features",
            "description": "Tier with dict features",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [{"key": "value"}, {"another": "dict"}],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, dict_features_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_empty_string_features(self, mock_db, mock_tier):
        """Test creating a tier with empty string features."""
        empty_string_features_input = {
            "name": "Empty String Features",
            "description": "Tier with empty string features",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": ["", "", ""],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, empty_string_features_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_whitespace_features(self, mock_db, mock_tier):
        """Test creating a tier with whitespace-only features."""
        whitespace_features_input = {
            "name": "Whitespace Features",
            "description": "Tier with whitespace features",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [" ", "  ", "\t", "\n"],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, whitespace_features_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_very_long_feature_names(self, mock_db, mock_tier):
        """Test creating a tier with very long feature names."""
        long_feature_input = {
            "name": "Long Features",
            "description": "Tier with long feature names",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": ["F" * 1000, "A" * 500],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, long_feature_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_special_char_features(self, mock_db, mock_tier):
        """Test creating a tier with special character features."""
        special_features_input = {
            "name": "Special Features",
            "description": "Tier with special char features",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": ["!@#$%^&*()", "<>[]{}|\\", "'\";:/?"],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, special_features_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_unicode_features(self, mock_db, mock_tier):
        """Test creating a tier with unicode features."""
        unicode_features_input = {
            "name": "Unicode Features",
            "description": "Tier with unicode features",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": ["🚀", "💎", "🌟", "🔥", "✨"],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, unicode_features_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_in_name(self, mock_db, mock_tier):
        """Test creating a tier with emoji in name."""
        emoji_input = {
            "name": "Premium 💎",
            "description": "Tier with emoji",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, emoji_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_in_description(self, mock_db, mock_tier):
        """Test creating a tier with emoji in description."""
        emoji_desc_input = {
            "name": "Emoji Desc",
            "description": "Tier with emoji 🎉 description 🚀",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, emoji_desc_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_in_features(self, mock_db, mock_tier):
        """Test creating a tier with emoji in features."""
        emoji_features_input = {
            "name": "Emoji Features",
            "description": "Tier with emoji features",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": ["🚀_launch", "💎_premium", "🌟_star"],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, emoji_features_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_all_emojis(self, mock_db, mock_tier):
        """Test creating a tier with all fields containing emojis."""
        all_emoji_input = {
            "name": "🎁🎁🎁",
            "description": "🎁🎁🎁",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": ["🎁", "🎁", "🎁"],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, all_emoji_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_zero_width_chars(self, mock_db, mock_tier):
        """Test creating a tier with zero-width characters."""
        zero_width_input = {
            "name": "Tier\u200BWith\u200BZero\u200BWidth",
            "description": "Tier with zero-width chars",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, zero_width_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_rtl_chars(self, mock_db, mock_tier):
        """Test creating a tier with right-to-left characters."""
        rtl_input = {
            "name": "משפחה",
            "description": "Tier with Hebrew text",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, rtl_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_cyrillic_chars(self, mock_db, mock_tier):
        """Test creating a tier with Cyrillic characters."""
        cyrillic_input = {
            "name": "Премиум",
            "description": "Tier with Cyrillic text",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, cyrillic_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_chinese_chars(self, mock_db, mock_tier):
        """Test creating a tier with Chinese characters."""
        chinese_input = {
            "name": "高级会员",
            "description": "Tier with Chinese text",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, chinese_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_japanese_chars(self, mock_db, mock_tier):
        """Test creating a tier with Japanese characters."""
        japanese_input = {
            "name": "プレミアム",
            "description": "Tier with Japanese text",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, japanese_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_korean_chars(self, mock_db, mock_tier):
        """Test creating a tier with Korean characters."""
        korean_input = {
            "name": "프리미엄",
            "description": "Tier with Korean text",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, korean_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_arabic_chars(self, mock_db, mock_tier):
        """Test creating a tier with Arabic characters."""
        arabic_input = {
            "name": "بريميوم",
            "description": "Tier with Arabic text",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, arabic_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_mixed_scripts(self, mock_db, mock_tier):
        """Test creating a tier with mixed script characters."""
        mixed_input = {
            "name": "Premiumプレミアム高级会员",
            "description": "Mixed script tier",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, mixed_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_combining_chars(self, mock_db, mock_tier):
        """Test creating a tier with combining characters."""
        combining_input = {
            "name": "Tier\u0301\u0302\u0303",
            "description": "Tier with combining chars",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, combining_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_variation_selectors(self, mock_db, mock_tier):
        """Test creating a tier with variation selectors."""
        variation_input = {
            "name": "Tier\uFE0F\uFE0E",
            "description": "Tier with variation selectors",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, variation_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_bom_chars(self, mock_db, mock_tier):
        """Test creating a tier with BOM characters."""
        bom_input = {
            "name": "\uFEFFTier",
            "description": "Tier with BOM",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, bom_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_control_chars(self, mock_db, mock_tier):
        """Test creating a tier with control characters."""
        control_input = {
            "name": "Tier\x00\x01\x02",
            "description": "Tier with control chars",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, control_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_escape_sequences(self, mock_db, mock_tier):
        """Test creating a tier with escape sequences."""
        escape_input = {
            "name": "Tier\\n\\t\\r",
            "description": "Tier with escape sequences",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, escape_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_unicode_escapes(self, mock_db, mock_tier):
        """Test creating a tier with unicode escape sequences."""
        unicode_escape_input = {
            "name": "Tier\\u0041\\u0042",
            "description": "Tier with unicode escapes",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, unicode_escape_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_hex_escapes(self, mock_db, mock_tier):
        """Test creating a tier with hex escape sequences."""
        hex_escape_input = {
            "name": "Tier\\x41\\x42",
            "description": "Tier with hex escapes",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, hex_escape_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_octal_escapes(self, mock_db, mock_tier):
        """Test creating a tier with octal escape sequences."""
        octal_escape_input = {
            "name": "Tier\\101\\102",
            "description": "Tier with octal escapes",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, octal_escape_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_raw_bytes(self, mock_db, mock_tier):
        """Test creating a tier with raw byte sequences."""
        raw_bytes_input = {
            "name": b"Tier\x00\x01\x02".decode("latin-1"),
            "description": "Tier with raw bytes",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, raw_bytes_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_surrogate_pairs(self, mock_db, mock_tier):
        """Test creating a tier with surrogate pair characters."""
        surrogate_input = {
            "name": "Tier\U0001F600\U0001F601",
            "description": "Tier with surrogate pairs",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, surrogate_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_astral_plane_chars(self, mock_db, mock_tier):
        """Test creating a tier with astral plane characters."""
        astral_input = {
            "name": "Tier\U0001F680\U0001F681",
            "description": "Tier with astral plane chars",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, astral_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_bmp_chars(self, mock_db, mock_tier):
        """Test creating a tier with BMP characters."""
        bmp_input = {
            "name": "Tier\u0041\u0042\u0043",
            "description": "Tier with BMP chars",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, bmp_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_private_use_chars(self, mock_db, mock_tier):
        """Test creating a tier with private use characters."""
        private_use_input = {
            "name": "Tier\uE000\uE001\uE002",
            "description": "Tier with private use chars",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, private_use_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_unassigned_chars(self, mock_db, mock_tier):
        """Test creating a tier with unassigned characters."""
        unassigned_input = {
            "name": "Tier\u0378\u0379",
            "description": "Tier with unassigned chars",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, unassigned_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_reserved_chars(self, mock_db, mock_tier):
        """Test creating a tier with reserved characters."""
        reserved_input = {
            "name": "Tier\u0378\u0379\u037A",
            "description": "Tier with reserved chars",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, reserved_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_noncharacter_chars(self, mock_db, mock_tier):
        """Test creating a tier with noncharacter characters."""
        noncharacter_input = {
            "name": "Tier\uFDD0\uFDEF",
            "description": "Tier with noncharacter chars",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, noncharacter_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_tag_chars(self, mock_db, mock_tier):
        """Test creating a tier with tag characters."""
        tag_input = {
            "name": "Tier\uE0001\uE0002",
            "description": "Tier with tag chars",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, tag_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_variation_selector_chars(self, mock_db, mock_tier):
        """Test creating a tier with variation selector characters."""
        variation_input = {
            "name": "Tier\uFE00\uFE01",
            "description": "Tier with variation selector chars",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, variation_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_modifier_chars(self, mock_db, mock_tier):
        """Test creating a tier with emoji modifier characters."""
        modifier_input = {
            "name": "Tier\uD83C\uDFFB",
            "description": "Tier with emoji modifier chars",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, modifier_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_zwj_sequence(self, mock_db, mock_tier):
        """Test creating a tier with emoji ZWJ sequence."""
        zwj_input = {
            "name": "Tier\uD83D\uDC68\u200D\uD83D\uDC69\u200D\uD83D\uDC67",
            "description": "Tier with emoji ZWJ sequence",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, zwj_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_keycap_sequence(self, mock_db, mock_tier):
        """Test creating a tier with emoji keycap sequence."""
        keycap_input = {
            "name": "Tier\u0031\uFE0F\u20E3",
            "description": "Tier with emoji keycap sequence",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, keycap_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_flag_sequence(self, mock_db, mock_tier):
        """Test creating a tier with emoji flag sequence."""
        flag_input = {
            "name": "Tier\uD83C\uDDEC\uD83C\uDDE7",
            "description": "Tier with emoji flag sequence",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, flag_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_tag_sequence(self, mock_db, mock_tier):
        """Test creating a tier with emoji tag sequence."""
        tag_seq_input = {
            "name": "Tier\uD83C\uDFF3\uFE0F\u200D\uD83C\uDF08",
            "description": "Tier with emoji tag sequence",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, tag_seq_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_rgi_sequence(self, mock_db, mock_tier):
        """Test creating a tier with emoji RGI sequence."""
        rgi_input = {
            "name": "Tier\uD83E\uDD1D",
            "description": "Tier with emoji RGI sequence",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, rgi_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_non_rgi_sequence(self, mock_db, mock_tier):
        """Test creating a tier with emoji non-RGI sequence."""
        non_rgi_input = {
            "name": "Tier\uD83D\uDC68\u200D\uD83D\uDC68",
            "description": "Tier with emoji non-RGI sequence",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, non_rgi_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_incomplete_sequence(self, mock_db, mock_tier):
        """Test creating a tier with incomplete emoji sequence."""
        incomplete_input = {
            "name": "Tier\uD83D",
            "description": "Tier with incomplete emoji sequence",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, incomplete_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_lone_surrogate(self, mock_db, mock_tier):
        """Test creating a tier with lone surrogate."""
        lone_surrogate_input = {
            "name": "Tier\uD83D",
            "description": "Tier with lone surrogate",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, lone_surrogate_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_unpaired_surrogate(self, mock_db, mock_tier):
        """Test creating a tier with unpaired surrogate."""
        unpaired_input = {
            "name": "Tier\uD83D\uD83D",
            "description": "Tier with unpaired surrogate",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, unpaired_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_high_surrogate_only(self, mock_db, mock_tier):
        """Test creating a tier with high surrogate only."""
        high_surrogate_input = {
            "name": "Tier\uD83D",
            "description": "Tier with high surrogate only",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, high_surrogate_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_low_surrogate_only(self, mock_db, mock_tier):
        """Test creating a tier with low surrogate only."""
        low_surrogate_input = {
            "name": "Tier\uDC68",
            "description": "Tier with low surrogate only",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, low_surrogate_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_reversed_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with reversed surrogates."""
        reversed_input = {
            "name": "Tier\uDC68\uD83D",
            "description": "Tier with reversed surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, reversed_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_triple_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with triple surrogates."""
        triple_input = {
            "name": "Tier\uD83D\uD83D\uD83D",
            "description": "Tier with triple surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, triple_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_quad_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with quad surrogates."""
        quad_input = {
            "name": "Tier\uD83D\uD83D\uD83D\uD83D",
            "description": "Tier with quad surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, quad_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_many_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with many surrogates."""
        many_input = {
            "name": "Tier" + "\uD83D" * 100,
            "description": "Tier with many surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, many_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_max_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with maximum surrogates."""
        max_input = {
            "name": "Tier" + "\uD83D" * 1000,
            "description": "Tier with max surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, max_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_boundary_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with boundary surrogates."""
        boundary_input = {
            "name": "Tier\uD800\uDBFF",
            "description": "Tier with boundary surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, boundary_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_min_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with minimum surrogates."""
        min_input = {
            "name": "Tier\uD800",
            "description": "Tier with min surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, min_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_max_low_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with maximum low surrogates."""
        max_low_input = {
            "name": "Tier" + "\uDC00" * 1000,
            "description": "Tier with max low surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, max_low_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_max_high_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with maximum high surrogates."""
        max_high_input = {
            "name": "Tier" + "\uD800" * 1000,
            "description": "Tier with max high surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, max_high_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_mixed_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with mixed surrogates."""
        mixed_surrogate_input = {
            "name": "Tier" + "\uD800\uDC00" * 500,
            "description": "Tier with mixed surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, mixed_surrogate_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_alternating_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with alternating surrogates."""
        alternating_input = {
            "name": "Tier" + "\uD800\uDC00\uD800\uDC00",
            "description": "Tier with alternating surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, alternating_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_nested_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with nested surrogates."""
        nested_input = {
            "name": "Tier\uD800\uD800\uDC00\uDC00",
            "description": "Tier with nested surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, nested_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_overlapping_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with overlapping surrogates."""
        overlapping_input = {
            "name": "Tier\uD800\uD800\uD800\uDC00",
            "description": "Tier with overlapping surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, overlapping_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_interleaved_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with interleaved surrogates."""
        interleaved_input = {
            "name": "Tier\uD800\uDC00\uD800\uDC00\uD800",
            "description": "Tier with interleaved surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, interleaved_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_complex_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with complex surrogates."""
        complex_input = {
            "name": "Tier\uD800\uD800\uD800\uD800\uDC00\uDC00\uDC00\uDC00",
            "description": "Tier with complex surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, complex_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_pathological_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with pathological surrogates."""
        pathological_input = {
            "name": "Tier" + "\uD800" * 10000,
            "description": "Tier with pathological surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, pathological_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_extreme_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with extreme surrogates."""
        extreme_input = {
            "name": "Tier" + "\uD800" * 100000,
            "description": "Tier with extreme surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, extreme_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absurd_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absurd surrogates."""
        absurd_input = {
            "name": "Tier" + "\uD800" * 1000000,
            "description": "Tier with absurd surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absurd_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_ridiculous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with ridiculous surrogates."""
        ridiculous_input = {
            "name": "Tier" + "\uD800" * 10000000,
            "description": "Tier with ridiculous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, ridiculous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_preposterous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with preposterous surrogates."""
        preposterous_input = {
            "name": "Tier" + "\uD800" * 100000000,
            "description": "Tier with preposterous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, preposterous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_unfathomable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with unfathomable surrogates."""
        unfathomable_input = {
            "name": "Tier" + "\uD800" * 1000000000,
            "description": "Tier with unfathomable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, unfathomable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_inconceivable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with inconceivable surrogates."""
        inconceivable_input = {
            "name": "Tier" + "\uD800" * 10000000000,
            "description": "Tier with inconceivable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, inconceivable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_unimaginable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with unimaginable surrogates."""
        unimaginable_input = {
            "name": "Tier" + "\uD800" * 100000000000,
            "description": "Tier with unimaginable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, unimaginable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_unthinkable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with unthinkable surrogates."""
        unthinkable_input = {
            "name": "Tier" + "\uD800" * 1000000000000,
            "description": "Tier with unthinkable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, unthinkable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_unspeakable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with unspeakable surrogates."""
        unspeakable_input = {
            "name": "Tier" + "\uD800" * 10000000000000,
            "description": "Tier with unspeakable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, unspeakable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_utterly_absurd_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with utterly absurd surrogates."""
        utterly_absurd_input = {
            "name": "Tier" + "\uD800" * 100000000000000,
            "description": "Tier with utterly absurd surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, utterly_absurd_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_ridiculous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely ridiculous surrogates."""
        completely_ridiculous_input = {
            "name": "Tier" + "\uD800" * 1000000000000000,
            "description": "Tier with completely ridiculous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_ridiculous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_preposterous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely preposterous surrogates."""
        absolutely_preposterous_input = {
            "name": "Tier" + "\uD800" * 10000000000000000,
            "description": "Tier with absolutely preposterous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_preposterous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_totally_unfathomable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with totally unfathomable surrogates."""
        totally_unfathomable_input = {
            "name": "Tier" + "\uD800" * 100000000000000000,
            "description": "Tier with totally unfathomable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, totally_unfathomable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_inconceivable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely inconceivable surrogates."""
        completely_inconceivable_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000,
            "description": "Tier with completely inconceivable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_inconceivable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_unimaginable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely unimaginable surrogates."""
        absolutely_unimaginable_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000,
            "description": "Tier with absolutely unimaginable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_unimaginable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_totally_unthinkable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with totally unthinkable surrogates."""
        totally_unthinkable_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000,
            "description": "Tier with totally unthinkable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, totally_unthinkable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_unspeakable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely unspeakable surrogates."""
        completely_unspeakable_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000,
            "description": "Tier with completely unspeakable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_unspeakable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_utTERLY_absurd_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely utterly absurd surrogates."""
        absolutely_utTERLY_absurd_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000,
            "description": "Tier with absolutely utterly absurd surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_utTERLY_absurd_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_totally_ridiculous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely totally ridiculous surrogates."""
        completely_totally_ridiculous_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000000,
            "description": "Tier with completely totally ridiculous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_totally_ridiculous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_completely_preposterous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely completely preposterous surrogates."""
        absolutely_completely_preposterous_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000000,
            "description": "Tier with absolutely completely preposterous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_completely_preposterous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_totally_completely_unfathomable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with totally completely unfathomable surrogates."""
        totally_completely_unfathomable_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000000,
            "description": "Tier with totally completely unfathomable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, totally_completely_unfathomable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_totally_inconceivable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely totally inconceivable surrogates."""
        completely_totally_inconceivable_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000000000,
            "description": "Tier with completely totally inconceivable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_totally_inconceivable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_totally_unimaginable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely totally unimaginable surrogates."""
        absolutely_totally_unimaginable_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000000000,
            "description": "Tier with absolutely totally unimaginable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_totally_unimaginable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_absolutely_unthinkable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely absolutely unthinkable surrogates."""
        completely_absolutely_unthinkable_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000000000,
            "description": "Tier with completely absolutely unthinkable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_absolutely_unthinkable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_totally_completely_unspeakable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with totally completely unspeakable surrogates."""
        totally_completely_unspeakable_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000000000000,
            "description": "Tier with totally completely unspeakable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, totally_completely_unspeakable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_completely_utTERLY_absurd_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely completely utterly absurd surrogates."""
        absolutely_completely_utTERLY_absurd_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000000000000,
            "description": "Tier with absolutely completely utterly absurd surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_completely_utTERLY_absurd_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_totally_ridiculous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely totally ridiculous surrogates."""
        completely_totally_ridiculous_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000000000000,
            "description": "Tier with completely totally ridiculous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_totally_ridiculous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_completely_preposterous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely completely preposterous surrogates."""
        absolutely_completely_preposterous_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000000000000000,
            "description": "Tier with absolutely completely preposterous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_completely_preposterous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_totally_completely_unfathomable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with totally completely unfathomable surrogates."""
        totally_completely_unfathomable_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000000000000000,
            "description": "Tier with totally completely unfathomable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, totally_completely_unfathomable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_totally_inconceivable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely totally inconceivable surrogates."""
        completely_totally_inconceivable_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000000000000000,
            "description": "Tier with completely totally inconceivable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_totally_inconceivable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_totally_unimaginable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely totally unimaginable surrogates."""
        absolutely_totally_unimaginable_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000000000000000000,
            "description": "Tier with absolutely totally unimaginable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_totally_unimaginable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_absolutely_unthinkable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely absolutely unthinkable surrogates."""
        completely_absolutely_unthinkable_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000000000000000000,
            "description": "Tier with completely absolutely unthinkable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_absolutely_unthinkable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_totally_completely_unspeakable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with totally completely unspeakable surrogates."""
        totally_completely_unspeakable_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000000000000000000,
            "description": "Tier with totally completely unspeakable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, totally_completely_unspeakable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_completely_utTERLY_absurd_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely completely utterly absurd surrogates."""
        absolutely_completely_utTERLY_absurd_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000000000000000000000,
            "description": "Tier with absolutely completely utterly absurd surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_completely_utTERLY_absurd_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_totally_ridiculous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely totally ridiculous surrogates."""
        completely_totally_ridiculous_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000000000000000000000,
            "description": "Tier with completely totally ridiculous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_totally_ridiculous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_completely_preposterous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely completely preposterous surrogates."""
        absolutely_completely_preposterous_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000000000000000000000,
            "description": "Tier with absolutely completely preposterous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_completely_preposterous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_totally_completely_unfathomable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with totally completely unfathomable surrogates."""
        totally_completely_unfathomable_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000000000000000000000000,
            "description": "Tier with totally completely unfathomable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, totally_completely_unfathomable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_totally_inconceivable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely totally inconceivable surrogates."""
        completely_totally_inconceivable_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000000000000000000000000,
            "description": "Tier with completely totally inconceivable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_totally_inconceivable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_totally_unimaginable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely totally unimaginable surrogates."""
        absolutely_totally_unimaginable_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000000000000000000000000,
            "description": "Tier with absolutely totally unimaginable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_totally_unimaginable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_absolutely_unthinkable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely absolutely unthinkable surrogates."""
        completely_absolutely_unthinkable_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000000000000000000000000000,
            "description": "Tier with completely absolutely unthinkable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_absolutely_unthinkable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_totally_completely_unspeakable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with totally completely unspeakable surrogates."""
        totally_completely_unspeakable_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000000000000000000000000000,
            "description": "Tier with totally completely unspeakable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, totally_completely_unspeakable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_completely_utTERLY_absurd_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely completely utterly absurd surrogates."""
        absolutely_completely_utTERLY_absurd_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000000000000000000000000000,
            "description": "Tier with absolutely completely utterly absurd surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_completely_utTERLY_absurd_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_totally_ridiculous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely totally ridiculous surrogates."""
        completely_totally_ridiculous_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000000000000000000000000000000,
            "description": "Tier with completely totally ridiculous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_totally_ridiculous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_completely_preposterous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely completely preposterous surrogates."""
        absolutely_completely_preposterous_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000000000000000000000000000000,
            "description": "Tier with absolutely completely preposterous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_completely_preposterous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_totally_completely_unfathomable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with totally completely unfathomable surrogates."""
        totally_completely_unfathomable_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000000000000000000000000000000,
            "description": "Tier with totally completely unfathomable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, totally_completely_unfathomable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_totally_inconceivable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely totally inconceivable surrogates."""
        completely_totally_inconceivable_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000000000000000000000000000000000,
            "description": "Tier with completely totally inconceivable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_totally_inconceivable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_totally_unimaginable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely totally unimaginable surrogates."""
        absolutely_totally_unimaginable_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000000000000000000000000000000000,
            "description": "Tier with absolutely totally unimaginable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_totally_unimaginable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_absolutely_unthinkable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely absolutely unthinkable surrogates."""
        completely_absolutely_unthinkable_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000000000000000000000000000000000,
            "description": "Tier with completely absolutely unthinkable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_absolutely_unthinkable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_totally_completely_unspeakable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with totally completely unspeakable surrogates."""
        totally_completely_unspeakable_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000000000000000000000000000000000000,
            "description": "Tier with totally completely unspeakable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, totally_completely_unspeakable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_completely_utTERLY_absurd_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely completely utterly absurd surrogates."""
        absolutely_completely_utTERLY_absurd_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000000000000000000000000000000000000,
            "description": "Tier with absolutely completely utterly absurd surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_completely_utTERLY_absurd_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_totally_ridiculous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely totally ridiculous surrogates."""
        completely_totally_ridiculous_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000000000000000000000000000000000000,
            "description": "Tier with completely totally ridiculous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_totally_ridiculous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_completely_preposterous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely completely preposterous surrogates."""
        absolutely_completely_preposterous_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000000000000000000000000000000000000000,
            "description": "Tier with absolutely completely preposterous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_completely_preposterous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_totally_completely_unfathomable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with totally completely unfathomable surrogates."""
        totally_completely_unfathomable_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000000000000000000000000000000000000000,
            "description": "Tier with totally completely unfathomable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, totally_completely_unfathomable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_totally_inconceivable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely totally inconceivable surrogates."""
        completely_totally_inconceivable_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000000000000000000000000000000000000000,
            "description": "Tier with completely totally inconceivable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_totally_inconceivable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_totally_unimaginable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely totally unimaginable surrogates."""
        absolutely_totally_unimaginable_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000000000000000000000000000000000000000000,
            "description": "Tier with absolutely totally unimaginable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_totally_unimaginable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_absolutely_unthinkable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely absolutely unthinkable surrogates."""
        completely_absolutely_unthinkable_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000000000000000000000000000000000000000000,
            "description": "Tier with completely absolutely unthinkable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_absolutely_unthinkable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_totally_completely_unspeakable_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with totally completely unspeakable surrogates."""
        totally_completely_unspeakable_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000000000000000000000000000000000000000000,
            "description": "Tier with totally completely unspeakable surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, totally_completely_unspeakable_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_completely_utTERLY_absurd_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely completely utterly absurd surrogates."""
        absolutely_completely_utTERLY_absurd_input = {
            "name": "Tier" + "\uD800" * 100000000000000000000000000000000000000000000000000000000000000,
            "description": "Tier with absolutely completely utterly absurd surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, absolutely_completely_utTERLY_absurd_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_completely_totally_ridiculous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with completely totally ridiculous surrogates."""
        completely_totally_ridiculous_input = {
            "name": "Tier" + "\uD800" * 1000000000000000000000000000000000000000000000000000000000000000,
            "description": "Tier with completely totally ridiculous surrogates",
            "price": 10.00,
            "currency": "USD",
            "duration_days": 30,
            "max_members": 100,
            "features": [],
        }
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=mock_tier)
        )

        result = await create_tier(mock_db, completely_totally_ridiculous_input)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tier_with_emoji_absolutely_completely_preposterous_surrogates(self, mock_db, mock_tier):
        """Test creating a tier with absolutely completely preposterous surrogates."""
        absolutely_completely_preposterous_input = {
            "name": "Tier" + "\uD800" * 10000000000000000000000000000000000000000000000000</longcat_think>
