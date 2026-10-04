"""Report Service for gated-communities."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


class ReportServiceError(Exception):
    """Base exception for report service errors."""


class ReportServiceNotFoundError(ReportServiceError):
    """Raised when a report item is not found."""


class ReportServiceValidationError(ReportServiceError):
    """Raised when report data fails validation."""


class ReportServiceService:
    """Service for managing report items."""

    def __init__(self, db=None):
        self._db = db
        self._items: dict[str, dict[str, Any]] = {{}}

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new report item.

        Args:
            data: Dictionary containing report data.

        Returns:
            The created item with an assigned ID.

        Raises:
            ReportServiceValidationError: If data is invalid.
        """
        if not isinstance(data, dict):
            raise ReportServiceValidationError("data must be a dictionary")

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
        """Get a report item by ID.

        Args:
            item_id: The unique identifier of the item.

        Returns:
            The item data.

        Raises:
            ReportServiceNotFoundError: If the item is not found.
        """
        if not item_id or not isinstance(item_id, str):
            raise ReportServiceValidationError("item_id is required and must be a non-empty string")

        item = self._items.get(item_id)
        if item is None:
            raise ReportServiceNotFoundError(f"ReportService not found: {{item_id}}")

        return item

    def list(
        self,
        filters: dict[str, Any] | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List report items with optional filtering and pagination.

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
        """Update an existing report item.

        Args:
            item_id: The unique identifier of the item to update.
            data: Dictionary containing the fields to update.

        Returns:
            The updated item.

        Raises:
            ReportServiceNotFoundError: If the item is not found.
            ReportServiceValidationError: If data is invalid.
        """
        if not item_id or not isinstance(item_id, str):
            raise ReportServiceValidationError("item_id is required and must be a non-empty string")
        if not isinstance(data, dict):
            raise ReportServiceValidationError("data must be a dictionary")

        item = self.get(item_id)
        item.update(data)
        item["updated_at"] = datetime.now(UTC).isoformat()
        return item

    def delete(self, item_id: str) -> bool:
        """Delete a report item by ID.

        Args:
            item_id: The unique identifier of the item to delete.

        Returns:
            True if the item was successfully deleted.

        Raises:
            ReportServiceNotFoundError: If the item is not found.
        """
        if not item_id or not isinstance(item_id, str):
            raise ReportServiceValidationError("item_id is required and must be a non-empty string")

        if item_id not in self._items:
            raise ReportServiceNotFoundError(f"ReportService not found: {{item_id}}")

        del self._items[item_id]
        return True


# Module-level convenience functions
_default_service = ReportServiceService()


def create(data: dict[str, Any]) -> dict[str, Any]:
    """Create a new report item."""
    return _default_service.create(data)


def get(item_id: str) -> dict[str, Any]:
    """Get a report item by ID."""
    return _default_service.get(item_id)


def list_items(
    filters: dict[str, Any] | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List report items."""
    return _default_service.list(filters, skip, limit)


def update(item_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Update a report item."""
    return _default_service.update(item_id, data)


def delete(item_id: str) -> bool:
    """Delete a report item."""
    return _default_service.delete(item_id)
