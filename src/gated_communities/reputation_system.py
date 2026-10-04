"""Reputation system module."""

from __future__ import annotations
from typing import Any


def calculate_reputation(user_id: str, community_id: str) -> dict[str, Any]:
    """Calculate reputation."""
    return {"user_id": user_id, "score": 100, "tier": "bronze"}


def get_reputation_score(user_id: str) -> int:
    """Get reputation score."""
    return 100


def update_reputation(user_id: str, delta: int, reason: str = "") -> dict[str, Any]:
    """Update reputation."""
    return {"user_id": user_id, "new_score": 100 + delta, "reason": reason}
