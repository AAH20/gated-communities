"""Fraud Service for gated-communities."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


class FraudServiceError(Exception):
    """Base exception for fraud service errors."""


class FraudServiceNotFoundError(FraudServiceError):
    """Raised when a fraud item is not found."""


class FraudServiceValidationError(FraudServiceError):
    """Raised when fraud data fails validation."""


class FraudServiceService:
    """Service for managing fraud items."""

    def __init__(self, db=None):
        self._db = db
        self._items: dict[str, dict[str, Any]] = {{}}

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new fraud item.

        Args:
            data: Dictionary containing fraud data.

        Returns:
            The created item with an assigned ID.

        Raises:
            FraudServiceValidationError: If data is invalid.
        """
        if not isinstance(data, dict):
            raise FraudServiceValidationError("data must be a dictionary")

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
        """Get a fraud item by ID.

        Args:
            item_id: The unique identifier of the item.

        Returns:
            The item data.

        Raises:
            FraudServiceNotFoundError: If the item is not found.
        """
        if not item_id or not isinstance(item_id, str):
            raise FraudServiceValidationError("item_id is required and must be a non-empty string")

        item = self._items.get(item_id)
        if item is None:
            raise FraudServiceNotFoundError(f"FraudService not found: {{item_id}}")

        return item

    def list(
        self,
        filters: dict[str, Any] | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List fraud items with optional filtering and pagination.

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
        """Update an existing fraud item.

        Args:
            item_id: The unique identifier of the item to update.
            data: Dictionary containing the fields to update.

        Returns:
            The updated item.

        Raises:
            FraudServiceNotFoundError: If the item is not found.
            FraudServiceValidationError: If data is invalid.
        """
        if not item_id or not isinstance(item_id, str):
            raise FraudServiceValidationError("item_id is required and must be a non-empty string")
        if not isinstance(data, dict):
            raise FraudServiceValidationError("data must be a dictionary")

        item = self.get(item_id)
        item.update(data)
        item["updated_at"] = datetime.now(UTC).isoformat()
        return item

    def delete(self, item_id: str) -> bool:
        """Delete a fraud item by ID.

        Args:
            item_id: The unique identifier of the item to delete.

        Returns:
            True if the item was successfully deleted.

        Raises:
            FraudServiceNotFoundError: If the item is not found.
        """
        if not item_id or not isinstance(item_id, str):
            raise FraudServiceValidationError("item_id is required and must be a non-empty string")

        if item_id not in self._items:
            raise FraudServiceNotFoundError(f"FraudService not found: {{item_id}}")

        del self._items[item_id]
        return True


# Module-level convenience functions
_default_service = FraudServiceService()


def create(data: dict[str, Any]) -> dict[str, Any]:
    """Create a new fraud item."""
    return _default_service.create(data)


def get(item_id: str) -> dict[str, Any]:
    """Get a fraud item by ID."""
    return _default_service.get(item_id)


def list_items(
    filters: dict[str, Any] | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List fraud items."""
    return _default_service.list(filters, skip, limit)


def update(item_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Update a fraud item."""
    return _default_service.update(item_id, data)


def delete(item_id: str) -> bool:
    """Delete a fraud item."""
    return _default_service.delete(item_id)
