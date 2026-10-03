"""Reputation system agent for gated communities.

This module provides functions to calculate, retrieve, and update
member reputation scores within a gated community platform.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# In-memory store for demonstration; replace with persistent storage in production.
_reputation_store: dict[str, float] = {}

# Action-to-delta mapping for reputation updates.
_ACTION_DELTAS: dict[str, float] = {
    "upvote": 1.0,
    "downvote": -1.0,
    "post_created": 2.0,
    "comment_created": 0.5,
    "report_filed": -3.0,
    "report_upheld": -5.0,
    "report_rejected": 1.0,
    "invite_accepted": 3.0,
    "moderation_action": -10.0,
}


def calculate_reputation(member_id: str) -> dict[str, Any]:
    """Calculate comprehensive reputation data for a member.

    Args:
        member_id: Unique identifier of the member.

    Returns:
        A dictionary containing:
            - member_id: The member's ID.
            - score: Current reputation score.
            - tier: Reputation tier label.
            - actions_count: Number of recorded actions.
            - breakdown: Per-action contribution breakdown.

    Raises:
        ValueError: If member_id is empty or not a string.
    """
    if not isinstance(member_id, str) or not member_id.strip():
        raise ValueError("member_id must be a non-empty string")

    score = _reputation_store.get(member_id, 0.0)

    if score >= 100.0:
        tier = "gold"
    elif score >= 50.0:
        tier = "silver"
    elif score >= 10.0:
        tier = "bronze"
    else:
        tier = "new"

    breakdown = {action: delta for action, delta in _ACTION_DELTAS.items()}

    return {
        "member_id": member_id,
        "score": score,
        "tier": tier,
        "actions_count": len(_ACTION_DELTAS),
        "breakdown": breakdown,
    }


def get_reputation_score(member_id: str) -> float:
    """Get the current reputation score for a member.

    Args:
        member_id: Unique identifier of the member.

    Returns:
        The member's reputation score as a float. Returns 0.0 if the
        member has no recorded reputation.

    Raises:
        ValueError: If member_id is empty or not a string.
    """
    if not isinstance(member_id, str) or not member_id.strip():
        raise ValueError("member_id must be a non-empty string")

    return _reputation_store.get(member_id, 0.0)


def update_reputation(member_id: str, action: str) -> bool:
    """Update a member's reputation based on an action.

    Args:
        member_id: Unique identifier of the member.
        action: The action that triggered the reputation change.
            Must be a key in _ACTION_DELTAS.

    Returns:
        True if the reputation was updated successfully, False otherwise.

    Raises:
        ValueError: If member_id is empty or not a string.
        ValueError: If action is not a recognised action type.
    """
    if not isinstance(member_id, str) or not member_id.strip():
        raise ValueError("member_id must be a non-empty string")

    if not isinstance(action, str) or action not in _ACTION_DELTAS:
        raise ValueError(f"Unknown action '{action}'. Valid actions: {list(_ACTION_DELTAS.keys())}")

    delta = _ACTION_DELTAS[action]
    current = _reputation_store.get(member_id, 0.0)
    new_score = current + delta
    _reputation_store[member_id] = new_score

    logger.info(
        "Reputation updated for member %s: action=%s, delta=%.1f, new_score=%.1f",
        member_id,
        action,
        delta,
        new_score,
    )

    return True
