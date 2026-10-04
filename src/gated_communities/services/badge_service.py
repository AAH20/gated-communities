"""Badge Service for gated-communities."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


class BadgeServiceError(Exception):
    """Base exception for badge service errors."""


class BadgeServiceNotFoundError(BadgeServiceError):
    """Raised when a badge item is not found."""


class BadgeServiceValidationError(BadgeServiceError):
    """Raised when badge data fails validation."""


class BadgeServiceService:
    """Service for managing badge items."""

    def __init__(self, db=None):
        self._db = db
        self._items: dict[str, dict[str, Any]] = {{}}

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new badge item.

        Args:
            data: Dictionary containing badge data.

        Returns:
            The created item with an assigned ID.

        Raises:
            BadgeServiceValidationError: If data is invalid.
        """
        if not isinstance(data, dict):
            raise BadgeServiceValidationError("data must be a dictionary")

        item_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        item = {{
            "id": item_id,
            "created_at": now,
            "updated_at": now,
            **data,
        }}
        self._items[item_id] = item
        return item

    def get(self, item_id: str) -> dict[str, Any]:
        """Get a badge item by ID.

        Args:
            item_id: The unique identifier of the item.

        Returns:
            The item data.

        Raises:
            BadgeServiceNotFoundError: If the item is not found.
        """
        if not item_id or not isinstance(item_id, str):
            raise BadgeServiceValidationError("item_id is required and must be a non-empty string")

        item = self._items.get(item_id)
        if item is None:
            raise BadgeServiceNotFoundError(f"BadgeService not found: {{item_id}}")

        return item

    def list(
        self,
        filters: dict[str, Any] | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List badge items with optional filtering and pagination.

        Args:
            filters: Optional filter criteria.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of matching items.
        """
        items = list(self._items.values())

        if filters:
            for key, value in filters.items():
                items = [i for i in items if i.get(key) == value]

        return items[skip : skip + limit]

    def update(self, item_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing badge item.

        Args:
            item_id: The unique identifier of the item to update.
            data: Dictionary containing the fields to update.

        Returns:
            The updated item.

        Raises:
            BadgeServiceNotFoundError: If the item is not found.
            BadgeServiceValidationError: If data is invalid.
        """
        if not item_id or not isinstance(item_id, str):
            raise BadgeServiceValidationError("item_id is required and must be a non-empty string")
        if not isinstance(data, dict):
            raise BadgeServiceValidationError("data must be a dictionary")

        item = self.get(item_id)
        item.update(data)
        item["updated_at"] = datetime.now(UTC).isoformat()
        return item

    def delete(self, item_id: str) -> bool:
        """Delete a badge item by ID.

        Args:
            item_id: The unique identifier of the item to delete.

        Returns:
            True if the item was successfully deleted.

        Raises:
            BadgeServiceNotFoundError: If the item is not found.
        """
        if not item_id or not isinstance(item_id, str):
            raise BadgeServiceValidationError("item_id is required and must be a non-empty string")

        if item_id not in self._items:
            raise BadgeServiceNotFoundError(f"BadgeService not found: {{item_id}}")

        del self._items[item_id]
        return True


# Module-level convenience functions
_default_service = BadgeServiceService()


def create(data: dict[str, Any]) -> dict[str, Any]:
    """Create a new badge item."""
    return _default_service.create(data)


def get(item_id: str) -> dict[str, Any]:
    """Get a badge item by ID."""
    return _default_service.get(item_id)


def list_items(
    filters: dict[str, Any] | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List badge items."""
    return _default_service.list(filters, skip, limit)


def update(item_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Update a badge item."""
    return _default_service.update(item_id, data)


def delete(item_id: str) -> bool:
    """Delete a badge item."""
    return _default_service.delete(item_id)
