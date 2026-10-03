"""Moderation service for gated communities.

Handles creation, retrieval, listing, resolution, and deletion of
moderation items such as reported content, flagged posts, and user appeals.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class ModerationError(Exception):
    """Base exception for moderation service errors."""


class ModerationItemNotFoundError(ModerationError):
    """Raised when a moderation item cannot be found."""


class ModerationItemAlreadyResolvedError(ModerationError):
    """Raised when attempting to resolve an already-resolved item."""


class InvalidModerationDecisionError(ModerationError):
    """Raised when an invalid resolution decision is provided."""


_VALID_DECISIONS = frozenset({"approve", "reject", "dismiss", "escalate"})

# In-memory store — replace with database persistence in production
_moderation_store: dict[str, dict[str, Any]] = {}


def get_moderation_item(item_id: str) -> dict[str, Any]:
    """Get a moderation item by its ID.

    Args:
        item_id: The unique identifier of the moderation item.

    Returns:
        A dictionary containing the moderation item data.

    Raises:
        ValueError: If ``item_id`` is not a non-empty string.
        ModerationItemNotFoundError: If no item exists with the given ID.
        ModerationError: If the item retrieval fails for any other reason.
    """
    if not item_id or not isinstance(item_id, str):
        raise ValueError("item_id must be a non-empty string")

    try:
        item = _moderation_store.get(item_id)
        if item is None:
            raise ModerationItemNotFoundError(
                f"Moderation item '{item_id}' not found"
            )
        return dict(item)
    except ModerationItemNotFoundError:
        raise
    except Exception as exc:
        logger.error("Failed to get moderation item %s: %s", item_id, exc)
        raise ModerationError(
            f"Failed to retrieve moderation item '{item_id}'"
        ) from exc


def list_moderation_items(
    filters: dict[str, Any],
    page: int,
    page_size: int,
) -> list[dict[str, Any]]:
    """List moderation items with optional filters and pagination.

    Args:
        filters: A dictionary of filter criteria (e.g. ``{"status": "pending"}``).
        page: The page number (1-indexed).
        page_size: The number of items per page.

    Returns:
        A list of moderation item dictionaries.

    Raises:
        ValueError: If ``page`` or ``page_size`` is not a positive integer,
            or if ``filters`` is not a dictionary.
        ModerationError: If the listing operation fails.
    """
    if not isinstance(page, int) or page < 1:
        raise ValueError("page must be a positive integer")
    if not isinstance(page_size, int) or page_size < 1:
        raise ValueError("page_size must be a positive integer")
    if not isinstance(filters, dict):
        raise ValueError("filters must be a dictionary")

    try:
        items = list(_moderation_store.values())

        # Apply filters
        for key, value in filters.items():
            items = [item for item in items if item.get(key) == value]

        # Sort by created_at descending (newest first)
        items.sort(key=lambda i: i.get("created_at", ""), reverse=True)

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        return [dict(item) for item in items[start:end]]
    except Exception as exc:
        logger.error("Failed to list moderation items: %s", exc)
        raise ModerationError("Failed to list moderation items") from exc


def create_moderation_item(data: dict[str, Any]) -> dict[str, Any]:
    """Create a new moderation item.

    Args:
        data: A dictionary containing the moderation item fields
            (e.g. ``community_id``, ``reporter_id``, ``target_type``,
            ``target_id``, ``reason``).

    Returns:
        The newly created moderation item as a dictionary.

    Raises:
        ValueError: If ``data`` is empty or missing required fields.
        ModerationError: If the creation operation fails.
    """
    if not isinstance(data, dict) or not data:
        raise ValueError("data must be a non-empty dictionary")

    required_fields = ("community_id", "reporter_id", "target_type", "target_id", "reason")
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    try:
        item_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        item: dict[str, Any] = {
            "id": item_id,
            "community_id": data["community_id"],
            "reporter_id": data["reporter_id"],
            "target_type": data["target_type"],
            "target_id": data["target_id"],
            "reason": data["reason"],
            "status": "pending",
            "decision": None,
            "moderator_id": None,
            "created_at": now,
            "resolved_at": None,
            "metadata": data.get("metadata", {}),
        }

        _moderation_store[item_id] = item
        return dict(item)
    except Exception as exc:
        logger.error("Failed to create moderation item: %s", exc)
        raise ModerationError("Failed to create moderation item") from exc


def resolve_moderation_item(item_id: str, decision: str) -> dict[str, Any]:
    """Resolve a moderation item with a decision.

    Args:
        item_id: The unique identifier of the moderation item.
        decision: The resolution decision. Must be one of
            ``"approve"``, ``"reject"``, ``"dismiss"``, or ``"escalate"``.

    Returns:
        The updated moderation item as a dictionary.

    Raises:
        ValueError: If ``item_id`` is empty or ``decision`` is invalid.
        ModerationItemNotFoundError: If no item exists with the given ID.
        ModerationItemAlreadyResolvedError: If the item is already resolved.
        ModerationError: If the resolution operation fails.
    """
    if not item_id or not isinstance(item_id, str):
        raise ValueError("item_id must be a non-empty string")
    if not decision or decision.lower() not in _VALID_DECISIONS:
        raise InvalidModerationDecisionError(
            f"Invalid decision '{decision}'. Must be one of: {sorted(_VALID_DECISIONS)}"
        )

    try:
        item = _moderation_store.get(item_id)
        if item is None:
            raise ModerationItemNotFoundError(
                f"Moderation item '{item_id}' not found"
            )
        if item.get("status") == "resolved":
            raise ModerationItemAlreadyResolvedError(
                f"Moderation item '{item_id}' is already resolved"
            )

        now = datetime.now(timezone.utc).isoformat()
        item["status"] = "resolved"
        item["decision"] = decision.lower()
        item["resolved_at"] = now

        return dict(item)
    except (ModerationItemNotFoundError, ModerationItemAlreadyResolvedError):
        raise
    except Exception as exc:
        logger.error("Failed to resolve moderation item %s: %s", item_id, exc)
        raise ModerationError(
            f"Failed to resolve moderation item '{item_id}'"
        ) from exc


def delete_moderation_item(item_id: str) -> bool:
    """Delete a moderation item by its ID.

    Args:
        item_id: The unique identifier of the moderation item.

    Returns:
        ``True`` if the item was successfully deleted.

    Raises:
        ValueError: If ``item_id`` is empty.
        ModerationItemNotFoundError: If no item exists with the given ID.
        ModerationError: If the deletion operation fails.
    """
    if not item_id or not isinstance(item_id, str):
        raise ValueError("item_id must be a non-empty string")

    try:
        if item_id not in _moderation_store:
            raise ModerationItemNotFoundError(
                f"Moderation item '{item_id}' not found"
            )
        del _moderation_store[item_id]
        return True
    except ModerationItemNotFoundError:
        raise
    except Exception as exc:
        logger.error("Failed to delete moderation item %s: %s", item_id, exc)
        raise ModerationError(
            f"Failed to delete moderation item '{item_id}'"
        ) from exc
