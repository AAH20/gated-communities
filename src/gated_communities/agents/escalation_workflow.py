"""Escalation workflow agent for gated-communities.

Provides functions to create, query, and resolve community escalations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

# In-memory store for demonstration purposes.
# In production, replace with a persistent backend (database, API, etc.).
_ESCALATIONS: dict[str, dict[str, Any]] = {}

_VALID_PRIORITIES = {"low", "medium", "high", "critical"}


def create_escalation(issue_id: str, priority: str) -> dict:
    """Create a new escalation for a given issue.

    Args:
        issue_id: Unique identifier of the issue to escalate.
        priority: Priority level of the escalation.
            Must be one of: "low", "medium", "high", "critical".

    Returns:
        A dictionary containing the escalation details:
            - escalation_id: Unique identifier for the escalation.
            - issue_id: The associated issue identifier.
            - priority: The priority level.
            - status: Initial status ("open").
            - created_at: ISO 8601 timestamp of creation.
            - resolved_at: None (not yet resolved).

    Raises:
        ValueError: If issue_id is empty or priority is invalid.
        TypeError: If arguments are not strings.
    """
    if not isinstance(issue_id, str):
        raise TypeError(f"issue_id must be a string, got {type(issue_id).__name__}")
    if not isinstance(priority, str):
        raise TypeError(f"priority must be a string, got {type(priority).__name__}")
    if not issue_id.strip():
        raise ValueError("issue_id must not be empty or whitespace")
    if priority.lower() not in _VALID_PRIORITIES:
        raise ValueError(
            f"Invalid priority '{priority}'. Must be one of: {', '.join(sorted(_VALID_PRIORITIES))}"
        )

    escalation_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    escalation = {
        "escalation_id": escalation_id,
        "issue_id": issue_id,
        "priority": priority.lower(),
        "status": "open",
        "created_at": now,
        "resolved_at": None,
    }

    _ESCALATIONS[escalation_id] = escalation
    return escalation


def get_escalation_status(escalation_id: str) -> dict:
    """Retrieve the current status of an escalation.

    Args:
        escalation_id: Unique identifier of the escalation.

    Returns:
        A dictionary containing the escalation details:
            - escalation_id: The escalation identifier.
            - issue_id: The associated issue identifier.
            - priority: The priority level.
            - status: Current status ("open" or "resolved").
            - created_at: ISO 8601 timestamp of creation.
            - resolved_at: ISO 8601 timestamp of resolution, or None.

    Raises:
        ValueError: If escalation_id is empty.
        TypeError: If escalation_id is not a string.
        KeyError: If no escalation exists with the given ID.
    """
    if not isinstance(escalation_id, str):
        raise TypeError(f"escalation_id must be a string, got {type(escalation_id).__name__}")
    if not escalation_id.strip():
        raise ValueError("escalation_id must not be empty or whitespace")
    if escalation_id not in _ESCALATIONS:
        raise KeyError(f"No escalation found with id '{escalation_id}'")

    return dict(_ESCALATIONS[escalation_id])


def resolve_escalation(escalation_id: str) -> bool:
    """Resolve an open escalation.

    Args:
        escalation_id: Unique identifier of the escalation to resolve.

    Returns:
        True if the escalation was successfully resolved.
        False if the escalation was already resolved.

    Raises:
        ValueError: If escalation_id is empty.
        TypeError: If escalation_id is not a string.
        KeyError: If no escalation exists with the given ID.
    """
    if not isinstance(escalation_id, str):
        raise TypeError(f"escalation_id must be a string, got {type(escalation_id).__name__}")
    if not escalation_id.strip():
        raise ValueError("escalation_id must not be empty or whitespace")
    if escalation_id not in _ESCALATIONS:
        raise KeyError(f"No escalation found with id '{escalation_id}'")

    escalation = _ESCALATIONS[escalation_id]

    if escalation["status"] == "resolved":
        return False

    escalation["status"] = "resolved"
    escalation["resolved_at"] = datetime.now(UTC).isoformat()
    return True
