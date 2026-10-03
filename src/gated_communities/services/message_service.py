"""Message service for gated-communities."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


class MessageNotFoundError(Exception):
    """Raised when a message is not found."""


class MessageValidationError(Exception):
    """Raised when message data is invalid."""


_MESSAGES: dict[str, dict[str, Any]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_message(message_id: str) -> dict:
    """Get a message by its ID.

    Args:
        message_id: The unique identifier of the message.

    Returns:
        The message data as a dictionary.

    Raises:
        MessageNotFoundError: If no message exists with the given ID.
        MessageValidationError: If message_id is empty or not a string.
    """
    if not isinstance(message_id, str) or not message_id.strip():
        raise MessageValidationError("message_id must be a non-empty string")

    message = _MESSAGES.get(message_id)
    if message is None:
        raise MessageNotFoundError(f"Message not found: {message_id}")

    return dict(message)


def list_messages(filters: dict, page: int, page_size: int) -> list[dict]:
    """List messages with optional filters and pagination.

    Args:
        filters: A dictionary of filter criteria (e.g. {"author_id": "..."}).
        page: The page number (1-indexed).
        page_size: The number of messages per page.

    Returns:
        A list of message dictionaries matching the filters.

    Raises:
        MessageValidationError: If page or page_size is invalid.
    """
    if not isinstance(page, int) or page < 1:
        raise MessageValidationError("page must be a positive integer")
    if not isinstance(page_size, int) or page_size < 1:
        raise MessageValidationError("page_size must be a positive integer")
    if not isinstance(filters, dict):
        raise MessageValidationError("filters must be a dictionary")

    results: list[dict] = []
    for msg in _MESSAGES.values():
        if all(msg.get(k) == v for k, v in filters.items()):
            results.append(dict(msg))

    start = (page - 1) * page_size
    end = start + page_size
    return results[start:end]


def create_message(data: dict) -> dict:
    """Create a new message.

    Args:
        data: A dictionary containing message fields. Must include 'content'.

    Returns:
        The created message data including generated id and timestamps.

    Raises:
        MessageValidationError: If data is invalid or missing required fields.
    """
    if not isinstance(data, dict):
        raise MessageValidationError("data must be a dictionary")
    if not data.get("content"):
        raise MessageValidationError("content is required")

    message_id = str(uuid.uuid4())
    now = _now()
    message = {
        "id": message_id,
        "content": data["content"],
        "author_id": data.get("author_id", ""),
        "community_id": data.get("community_id", ""),
        "created_at": now,
        "updated_at": now,
    }
    _MESSAGES[message_id] = message
    return dict(message)


def update_message(message_id: str, data: dict) -> dict:
    """Update an existing message.

    Args:
        message_id: The unique identifier of the message to update.
        data: A dictionary of fields to update.

    Returns:
        The updated message data.

    Raises:
        MessageNotFoundError: If no message exists with the given ID.
        MessageValidationError: If message_id or data is invalid.
    """
    if not isinstance(message_id, str) or not message_id.strip():
        raise MessageValidationError("message_id must be a non-empty string")
    if not isinstance(data, dict):
        raise MessageValidationError("data must be a dictionary")

    message = _MESSAGES.get(message_id)
    if message is None:
        raise MessageNotFoundError(f"Message not found: {message_id}")

    for key, value in data.items():
        if key != "id":
            message[key] = value
    message["updated_at"] = _now()
    return dict(message)


def delete_message(message_id: str) -> bool:
    """Delete a message by its ID.

    Args:
        message_id: The unique identifier of the message to delete.

    Returns:
        True if the message was deleted.

    Raises:
        MessageNotFoundError: If no message exists with the given ID.
        MessageValidationError: If message_id is invalid.
    """
    if not isinstance(message_id, str) or not message_id.strip():
        raise MessageValidationError("message_id must be a non-empty string")

    if message_id not in _MESSAGES:
        raise MessageNotFoundError(f"Message not found: {message_id}")

    del _MESSAGES[message_id]
    return True
