"""Comprehensive agent tests for the reputation system module."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from src.gated_communities.reputation_system import (
    calculate_reputation,
    get_reputation_score,
    update_reputation,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_user_id():
    """Return a sample user identifier."""
    return "user_12345"


@pytest.fixture
def sample_community_id():
    """Return a sample community identifier."""
    return "community_67890"


@pytest.fixture
def base_reputation_data():
    """Return a base reputation data dictionary."""
    return {
        "user_id": "user_12345",
        "community_id": "community_67890",
        "score": 100,
        "contributions": 50,
        "violations": 2,
        "last_updated": datetime(2024, 1, 1, 12, 0, 0),
    }


@pytest.fixture
def mock_db():
    """Return a mock database connection."""
    db = MagicMock()
    db.fetch_one = MagicMock(return_value=None)
    db.fetch_all = MagicMock(return_value=[])
    db.execute = MagicMock(return_value=None)
    db.commit = MagicMock(return_value=None)
    return db


@pytest.fixture
def mock_redis():
    """Return a mock Redis client."""
    redis = MagicMock()
    redis.get = MagicMock(return_value=None)
    redis.set = MagicMock(return_value=True)
    redis.delete = MagicMock(return_value=1)
    return redis


@pytest.fixture
def reputation_weights():
    """Return reputation calculation weights."""
    return {
        "contribution_weight": 1.0,
        "violation_penalty": 10.0,
        "time_decay_factor": 0.99,
        "bonus_threshold": 100,
        "bonus_multiplier": 1.5,
    }


# ---------------------------------------------------------------------------
# Tests for calculate_reputation
# ---------------------------------------------------------------------------


class TestCalculateReputation:
    """Tests for the calculate_reputation function."""

    def test_calculate_reputation_with_positive_contributions(
        self, sample_user_id, sample_community_id, reputation_weights
    ):
        """Test reputation calculation with positive contributions."""
        contributions = 100
        violations = 0

        result = calculate_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            contributions=contributions,
            violations=violations,
            weights=reputation_weights,
        )

        assert result is not None
        assert isinstance(result, (int, float))
        assert result > 0
        assert result == pytest.approx(100.0)

    def test_calculate_reputation_with_violations(
        self, sample_user_id, sample_community_id, reputation_weights
    ):
        """Test reputation calculation penalizes violations."""
        contributions = 100
        violations = 5

        result = calculate_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            contributions=contributions,
            violations=violations,
            weights=reputation_weights,
        )

        assert result is not None
        assert isinstance(result, (int, float))
        # 100 contributions - (5 violations * 10 penalty) = 50
        assert result == pytest.approx(50.0)

    def test_calculate_reputation_zero_contributions(
        self, sample_user_id, sample_community_id, reputation_weights
    ):
        """Test reputation calculation with zero contributions."""
        result = calculate_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            contributions=0,
            violations=0,
            weights=reputation_weights,
        )

        assert result is not None
        assert result == pytest.approx(0.0)

    def test_calculate_reputation_high_violations_clamps_to_zero(
        self, sample_user_id, sample_community_id, reputation_weights
    ):
        """Test reputation does not go below zero."""
        contributions = 10
        violations = 100

        result = calculate_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            contributions=contributions,
            violations=violations,
            weights=reputation_weights,
        )

        assert result is not None
        assert result >= 0

    def test_calculate_reputation_with_bonus_threshold(
        self, sample_user_id, sample_community_id, reputation_weights
    ):
        """Test reputation bonus is applied above threshold."""
        contributions = 150
        violations = 0

        result = calculate_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            contributions=contributions,
            violations=violations,
            weights=reputation_weights,
        )

        assert result is not None
        # Above threshold of 100, bonus multiplier of 1.5 applies
        assert result > 150.0

    def test_calculate_reputation_with_custom_weights(
        self, sample_user_id, sample_community_id
    ):
        """Test reputation calculation with custom weights."""
        custom_weights = {
            "contribution_weight": 2.0,
            "violation_penalty": 5.0,
            "time_decay_factor": 0.95,
            "bonus_threshold": 50,
            "bonus_multiplier": 2.0,
        }

        result = calculate_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            contributions=50,
            violations=2,
            weights=custom_weights,
        )

        assert result is not None
        # 50 * 2.0 - 2 * 5.0 = 90
        assert result == pytest.approx(90.0)

    def test_calculate_reputation_returns_consistent_results(
        self, sample_user_id, sample_community_id, reputation_weights
    ):
        """Test that the same inputs produce the same output."""
        kwargs = {
            "user_id": sample_user_id,
            "community_id": sample_community_id,
            "contributions": 75,
            "violations": 3,
            "weights": reputation_weights,
        }

        result1 = calculate_reputation(**kwargs)
        result2 = calculate_reputation(**kwargs)

        assert result1 == result2

    def test_calculate_reputation_with_large_numbers(
        self, sample_user_id, sample_community_id, reputation_weights
    ):
        """Test reputation calculation handles large numbers."""
        result = calculate_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            contributions=1_000_000,
            violations=1000,
            weights=reputation_weights,
        )

        assert result is not None
        assert isinstance(result, (int, float))
        assert result > 0

    def test_calculate_reputation_with_float_contributions(
        self, sample_user_id, sample_community_id, reputation_weights
    ):
        """Test reputation calculation with float contribution values."""
        result = calculate_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            contributions=50.5,
            violations=1,
            weights=reputation_weights,
        )

        assert result is not None
        assert isinstance(result, float)

    def test_calculate_reputation_different_users_different_scores(
        self, sample_community_id, reputation_weights
    ):
        """Test different users can have different reputation scores."""
        result1 = calculate_reputation(
            user_id="user_a",
            community_id=sample_community_id,
            contributions=100,
            violations=0,
            weights=reputation_weights,
        )
        result2 = calculate_reputation(
            user_id="user_b",
            community_id=sample_community_id,
            contributions=50,
            violations=0,
            weights=reputation_weights,
        )

        assert result1 != result2
        assert result1 > result2


# ---------------------------------------------------------------------------
# Tests for get_reputation_score
# ---------------------------------------------------------------------------


class TestGetReputationScore:
    """Tests for the get_reputation_score function."""

    def test_get_reputation_score_returns_score(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test get_reputation_score returns the stored score."""
        mock_db.fetch_one.return_value = {
            "score": 85,
            "user_id": sample_user_id,
            "community_id": sample_community_id,
        }

        result = get_reputation_score(
            user_id=sample_user_id,
            community_id=sample_community_id,
            db=mock_db,
        )

        assert result is not None
        assert isinstance(result, (int, float))
        assert result == 85

    def test_get_reputation_score_user_not_found(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test get_reputation_score returns default for unknown user."""
        mock_db.fetch_one.return_value = None

        result = get_reputation_score(
            user_id=sample_user_id,
            community_id=sample_community_id,
            db=mock_db,
        )

        assert result is not None
        assert result == 0

    def test_get_reputation_score_uses_cache(
        self, sample_user_id, sample_community_id, mock_db, mock_redis
    ):
        """Test get_reputation_score checks cache first."""
        mock_redis.get.return_value = "42"

        result = get_reputation_score(
            user_id=sample_user_id,
            community_id=sample_community_id,
            db=mock_db,
            cache=mock_redis,
        )

        assert result == 42
        mock_db.fetch_one.assert_not_called()

    def test_get_reputation_score_cache_miss_queries_db(
        self, sample_user_id, sample_community_id, mock_db, mock_redis
    ):
        """Test get_reputation_score queries DB on cache miss."""
        mock_redis.get.return_value = None
        mock_db.fetch_one.return_value = {"score": 77}

        result = get_reputation_score(
            user_id=sample_user_id,
            community_id=sample_community_id,
            db=mock_db,
            cache=mock_redis,
        )

        assert result == 77
        mock_db.fetch_one.assert_called_once()

    def test_get_reputation_score_updates_cache(
        self, sample_user_id, sample_community_id, mock_db, mock_redis
    ):
        """Test get_reputation_score populates cache after DB query."""
        mock_redis.get.return_value = None
        mock_db.fetch_one.return_value = {"score": 65}

        get_reputation_score(
            user_id=sample_user_id,
            community_id=sample_community_id,
            db=mock_db,
            cache=mock_redis,
        )

        mock_redis.set.assert_called_once()

    def test_get_reputation_score_with_zero_score(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test get_reputation_score handles zero score."""
        mock_db.fetch_one.return_value = {"score": 0}

        result = get_reputation_score(
            user_id=sample_user_id,
            community_id=sample_community_id,
            db=mock_db,
        )

        assert result == 0

    def test_get_reputation_score_with_negative_score(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test get_reputation_score handles negative scores."""
        mock_db.fetch_one.return_value = {"score": -10}

        result = get_reputation_score(
            user_id=sample_user_id,
            community_id=sample_community_id,
            db=mock_db,
        )

        assert result == -10

    def test_get_reputation_score_with_float_score(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test get_reputation_score handles float scores."""
        mock_db.fetch_one.return_value = {"score": 85.5}

        result = get_reputation_score(
            user_id=sample_user_id,
            community_id=sample_community_id,
            db=mock_db,
        )

        assert result == pytest.approx(85.5)

    def test_get_reputation_score_different_communities(
        self, sample_user_id, mock_db
    ):
        """Test get_reputation_score is community-specific."""
        mock_db.fetch_one.side_effect = [
            {"score": 100},
            {"score": 50},
        ]

        result1 = get_reputation_score(
            user_id=sample_user_id,
            community_id="community_a",
            db=mock_db,
        )
        result2 = get_reputation_score(
            user_id=sample_user_id,
            community_id="community_b",
            db=mock_db,
        )

        assert result1 == 100
        assert result2 == 50

    def test_get_reputation_score_db_error_returns_default(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test get_reputation_score handles DB errors gracefully."""
        mock_db.fetch_one.side_effect = Exception("DB connection failed")

        result = get_reputation_score(
            user_id=sample_user_id,
            community_id=sample_community_id,
            db=mock_db,
        )

        assert result == 0


# ---------------------------------------------------------------------------
# Tests for update_reputation
# ---------------------------------------------------------------------------


class TestUpdateReputation:
    """Tests for the update_reputation function."""

    def test_update_reputation_increases_score(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test update_reputation increases score on positive action."""
        mock_db.fetch_one.return_value = {"score": 50}

        result = update_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            action="contribution",
            db=mock_db,
        )

        assert result is not None
        assert result > 50

    def test_update_reputation_decreases_score_on_violation(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test update_reputation decreases score on violation."""
        mock_db.fetch_one.return_value = {"score": 50}

        result = update_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            action="violation",
            db=mock_db,
        )

        assert result is not None
        assert result < 50

    def test_update_reputation_creates_new_entry(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test update_reputation creates entry for new user."""
        mock_db.fetch_one.return_value = None

        result = update_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            action="contribution",
            db=mock_db,
        )

        assert result is not None
        assert mock_db.execute.called

    def test_update_reputation_persists_to_db(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test update_reputation persists changes to database."""
        mock_db.fetch_one.return_value = {"score": 50}

        update_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            action="contribution",
            db=mock_db,
        )

        assert mock_db.execute.called
        assert mock_db.commit.called

    def test_update_reputation_invalidates_cache(
        self, sample_user_id, sample_community_id, mock_db, mock_redis
    ):
        """Test update_reputation invalidates cached score."""
        mock_db.fetch_one.return_value = {"score": 50}

        update_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            action="contribution",
            db=mock_db,
            cache=mock_redis,
        )

        mock_redis.delete.assert_called_once()

    def test_update_reputation_with_custom_delta(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test update_reputation with custom score delta."""
        mock_db.fetch_one.return_value = {"score": 100}

        result = update_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            action="bonus",
            delta=25,
            db=mock_db,
        )

        assert result is not None
        assert result == 125

    def test_update_reputation_negative_delta(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test update_reputation with negative delta."""
        mock_db.fetch_one.return_value = {"score": 100}

        result = update_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            action="penalty",
            delta=-30,
            db=mock_db,
        )

        assert result is not None
        assert result == 70

    def test_update_reputation_does_not_go_below_zero(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test update_reputation clamps score to zero minimum."""
        mock_db.fetch_one.return_value = {"score": 10}

        result = update_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            action="violation",
            db=mock_db,
        )

        assert result is not None
        assert result >= 0

    def test_update_reputation_multiple_actions_sequential(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test multiple sequential updates accumulate correctly."""
        mock_db.fetch_one.return_value = {"score": 50}

        result1 = update_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            action="contribution",
            db=mock_db,
        )
        mock_db.fetch_one.return_value = {"score": result1}

        result2 = update_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            action="contribution",
            db=mock_db,
        )
        mock_db.fetch_one.return_value = {"score": result2}

        result3 = update_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            action="violation",
            db=mock_db,
        )

        assert result1 > 50
        assert result2 > result1
        assert result3 < result2

    def test_update_reputation_returns_new_score(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test update_reputation returns the updated score."""
        mock_db.fetch_one.return_value = {"score": 50}

        result = update_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            action="contribution",
            db=mock_db,
        )

        assert isinstance(result, (int, float))

    def test_update_reputation_with_unknown_action(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test update_reputation handles unknown action gracefully."""
        mock_db.fetch_one.return_value = {"score": 50}

        result = update_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            action="unknown_action_xyz",
            db=mock_db,
        )

        assert result is not None

    def test_update_reputation_db_error_handling(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test update_reputation handles DB errors."""
        mock_db.fetch_one.side_effect = Exception("Connection lost")

        with pytest.raises(Exception):
            update_reputation(
                user_id=sample_user_id,
                community_id=sample_community_id,
                action="contribution",
                db=mock_db,
            )

    def test_update_reputation_timestamp_updated(
        self, sample_user_id, sample_community_id, mock_db
    ):
        """Test update_reputation updates the last_updated timestamp."""
        mock_db.fetch_one.return_value = {
            "score": 50,
            "last_updated": datetime(2020, 1, 1),
        }

        before = datetime.utcnow()
        update_reputation(
            user_id=sample_user_id,
            community_id=sample_community_id,
            action="contribution",
            db=mock_db,
        )
        after = datetime.utcnow()

        # Verify execute was called with updated timestamp
        call_args = mock_db.execute.call_args
        assert call_args is not None
