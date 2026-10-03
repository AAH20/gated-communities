"""Invitation service for managing community invitations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


class InvitationNotFoundError(Exception):
    """Raised when an invitation cannot be found."""


class InvitationValidationError(Exception):
    """Raised when invitation data fails validation."""


class InvitationService:
    """Service for managing community invitations."""

    def __init__(self, db: Any = None) -> None:
        """Initialize the invitation service.

        Args:
            db: Optional database/persistence backend.
        """
        self._db = db
        self._invitations: dict[str, dict[str, Any]] = {}

    def get_invitation(self, invitation_id: str) -> dict:
        """Get an invitation by its ID.

        Args:
            invitation_id: The unique identifier of the invitation.

        Returns:
            The invitation data as a dictionary.

        Raises:
            InvitationNotFoundError: If no invitation exists with the given ID.
            InvitationValidationError: If the invitation_id is empty or invalid.
        """
        if not invitation_id or not isinstance(invitation_id, str):
            raise InvitationValidationError("invitation_id must be a non-empty string")

        invitation = self._invitations.get(invitation_id)
        if invitation is None:
            raise InvitationNotFoundError(f"Invitation with id '{invitation_id}' not found")
        return dict(invitation)

    def list_invitations(
        self,
        filters: dict | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[dict]:
        """List invitations with optional filtering and pagination.

        Args:
            filters: Optional dictionary of filter criteria (e.g. status, role).
            page: Page number (1-indexed).
            page_size: Number of results per page.

        Returns:
            A list of invitation dictionaries matching the criteria.

        Raises:
            InvitationValidationError: If page or page_size is invalid.
        """
        if page < 1:
            raise InvitationValidationError("page must be >= 1")
        if page_size < 1:
            raise InvitationValidationError("page_size must be >= 1")

        filters = filters or {}
        results: list[dict[str, Any]] = []

        for invitation in self._invitations.values():
            if self._matches_filters(invitation, filters):
                results.append(dict(invitation))

        start = (page - 1) * page_size
        end = start + page_size
        return results[start:end]

    def create_invitation(self, data: dict) -> dict:
        """Create a new invitation.

        Args:
            data: Dictionary containing invitation fields (e.g. email, role, community_id).

        Returns:
            The created invitation data including generated id and timestamps.

        Raises:
            InvitationValidationError: If required fields are missing or data is invalid.
        """
        if not isinstance(data, dict):
            raise InvitationValidationError("data must be a dictionary")

        if not data.get("email"):
            raise InvitationValidationError("email is required")
        if not data.get("community_id"):
            raise InvitationValidationError("community_id is required")

        invitation_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        invitation: dict[str, Any] = {
            "id": invitation_id,
            "email": data["email"],
            "community_id": data["community_id"],
            "role": data.get("role", "member"),
            "status": data.get("status", "pending"),
            "created_at": now,
            "updated_at": now,
            "expires_at": data.get("expires_at"),
            "metadata": data.get("metadata", {}),
        }

        self._invitations[invitation_id] = invitation
        return dict(invitation)

    def update_invitation(self, invitation_id: str, data: dict) -> dict:
        """Update an existing invitation.

        Args:
            invitation_id: The unique identifier of the invitation to update.
            data: Dictionary of fields to update.

        Returns:
            The updated invitation data.

        Raises:
            InvitationNotFoundError: If no invitation exists with the given ID.
            InvitationValidationError: If the data is invalid.
        """
        if not invitation_id or not isinstance(invitation_id, str):
            raise InvitationValidationError("invitation_id must be a non-empty string")
        if not isinstance(data, dict):
            raise InvitationValidationError("data must be a dictionary")

        invitation = self._invitations.get(invitation_id)
        if invitation is None:
            raise InvitationNotFoundError(f"Invitation with id '{invitation_id}' not found")

        allowed_fields = {"email", "role", "status", "expires_at", "metadata"}
        for key, value in data.items():
            if key in allowed_fields:
                invitation[key] = value

        invitation["updated_at"] = datetime.now(UTC).isoformat()
        return dict(invitation)

    def delete_invitation(self, invitation_id: str) -> bool:
        """Delete an invitation by its ID.

        Args:
            invitation_id: The unique identifier of the invitation to delete.

        Returns:
            True if the invitation was deleted, False if it did not exist.

        Raises:
            InvitationValidationError: If the invitation_id is empty or invalid.
        """
        if not invitation_id or not isinstance(invitation_id, str):
            raise InvitationValidationError("invitation_id must be a non-empty string")

        if invitation_id in self._invitations:
            del self._invitations[invitation_id]
            return True
        return False

    def _matches_filters(self, invitation: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Check if an invitation matches the given filter criteria.

        Args:
            invitation: The invitation dictionary to check.
            filters: Dictionary of field-value pairs to match.

        Returns:
            True if the invitation matches all filters, False otherwise.
        """
        for key, value in filters.items():
            if invitation.get(key) != value:
                return False
        return True
