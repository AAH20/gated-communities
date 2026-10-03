"""Event service for managing gated-community events."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


class EventServiceError(Exception):
    """Base exception for event service errors."""


class EventNotFoundError(EventServiceError):
    """Raised when an event is not found."""


class EventValidationError(EventServiceError):
    """Raised when event data fails validation."""


class EventService:
    """Service for CRUD operations on community events."""

    def __init__(self) -> None:
        """Initialize the event service with an in-memory store."""
        self._events: dict[str, dict[str, Any]] = {}

    def get_event(self, event_id: str) -> dict:
        """Get an event by its ID.

        Args:
            event_id: The unique identifier of the event.

        Returns:
            The event data as a dictionary.

        Raises:
            EventNotFoundError: If no event exists with the given ID.
            EventValidationError: If event_id is empty or invalid.
        """
        if not event_id or not isinstance(event_id, str):
            raise EventValidationError("event_id must be a non-empty string")

        event = self._events.get(event_id)
        if event is None:
            raise EventNotFoundError(f"Event with id '{event_id}' not found")

        return event.copy()

    def list_events(
        self,
        filters: dict | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[dict]:
        """List events with optional filtering and pagination.

        Args:
            filters: Optional dictionary of filter criteria (e.g., status, community_id).
            page: Page number (1-indexed).
            page_size: Number of events per page.

        Returns:
            A list of event dictionaries matching the filters.

        Raises:
            EventValidationError: If page or page_size is invalid.
        """
        if page < 1:
            raise EventValidationError("page must be >= 1")
        if page_size < 1:
            raise EventValidationError("page_size must be >= 1")

        filters = filters or {}
        events = list(self._events.values())

        # Apply filters
        filtered_events: list[dict] = []
        for event in events:
            match = True
            for key, value in filters.items():
                if key in event and event[key] != value:
                    match = False
                    break
            if match:
                filtered_events.append(event.copy())

        # Sort by created_at descending
        filtered_events.sort(
            key=lambda e: e.get("created_at", ""),
            reverse=True,
        )

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        return filtered_events[start:end]

    def create_event(self, data: dict) -> dict:
        """Create a new event.

        Args:
            data: Dictionary containing event fields (title, description, community_id, etc.).

        Returns:
            The created event data including generated id and timestamps.

        Raises:
            EventValidationError: If required fields are missing or data is invalid.
        """
        if not isinstance(data, dict):
            raise EventValidationError("data must be a dictionary")

        required_fields = ["title", "community_id"]
        for field in required_fields:
            if field not in data or not data[field]:
                raise EventValidationError(f"Missing required field: {field}")

        event_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        event: dict[str, Any] = {
            "id": event_id,
            "title": data["title"],
            "community_id": data["community_id"],
            "description": data.get("description", ""),
            "status": data.get("status", "draft"),
            "created_at": now,
            "updated_at": now,
            "metadata": data.get("metadata", {}),
        }

        # Add any extra fields from data
        for key, value in data.items():
            if key not in event:
                event[key] = value

        self._events[event_id] = event
        return event.copy()

    def update_event(self, event_id: str, data: dict) -> dict:
        """Update an existing event.

        Args:
            event_id: The unique identifier of the event to update.
            data: Dictionary containing fields to update.

        Returns:
            The updated event data.

        Raises:
            EventNotFoundError: If no event exists with the given ID.
            EventValidationError: If event_id is empty or data is invalid.
        """
        if not event_id or not isinstance(event_id, str):
            raise EventValidationError("event_id must be a non-empty string")
        if not isinstance(data, dict):
            raise EventValidationError("data must be a dictionary")

        event = self._events.get(event_id)
        if event is None:
            raise EventNotFoundError(f"Event with id '{event_id}' not found")

        # Prevent changing the id
        data = {k: v for k, v in data.items() if k != "id"}

        event.update(data)
        event["updated_at"] = datetime.now(UTC).isoformat()

        return event.copy()

    def delete_event(self, event_id: str) -> bool:
        """Delete an event by its ID.

        Args:
            event_id: The unique identifier of the event to delete.

        Returns:
            True if the event was deleted, False if it did not exist.

        Raises:
            EventValidationError: If event_id is empty or invalid.
        """
        if not event_id or not isinstance(event_id, str):
            raise EventValidationError("event_id must be a non-empty string")

        if event_id in self._events:
            del self._events[event_id]
            return True
        return False
