"""Member service for gated communities."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MemberNotFoundError(Exception):
    """Raised when a member is not found."""


class MemberServiceError(Exception):
    """Raised for general member service errors."""


class MemberService:
    """Service for managing members in gated communities."""

    def __init__(self, db: Any = None) -> None:
        """Initialize the member service.

        Args:
            db: Database or repository instance for member persistence.
        """
        self._db = db

    def get_member(self, member_id: str) -> dict:
        """Get a member by ID.

        Args:
            member_id: The unique identifier of the member.

        Returns:
            A dictionary containing the member data.

        Raises:
            MemberNotFoundError: If the member is not found.
            MemberServiceError: If an error occurs while fetching the member.
        """
        try:
            if self._db is None:
                raise MemberNotFoundError(f"Member '{member_id}' not found")
            member = self._db.get_member(member_id)
            if member is None:
                raise MemberNotFoundError(f"Member '{member_id}' not found")
            return member
        except MemberNotFoundError:
            raise
        except Exception as exc:
            logger.error("Error fetching member '%s': %s", member_id, exc)
            raise MemberServiceError(f"Failed to fetch member '{member_id}': {exc}") from exc

    def list_members(
        self, filters: dict, page: int, page_size: int
    ) -> list[dict]:
        """List members with optional filters and pagination.

        Args:
            filters: A dictionary of filter criteria.
            page: The page number (1-indexed).
            page_size: The number of members per page.

        Returns:
            A list of member dictionaries.

        Raises:
            MemberServiceError: If an error occurs while listing members.
        """
        try:
            if self._db is None:
                return []
            offset = (page - 1) * page_size
            return self._db.list_members(filters=filters, offset=offset, limit=page_size)
        except Exception as exc:
            logger.error("Error listing members: %s", exc)
            raise MemberServiceError(f"Failed to list members: {exc}") from exc

    def create_member(self, data: dict) -> dict:
        """Create a new member.

        Args:
            data: A dictionary containing the member data.

        Returns:
            A dictionary containing the created member data.

        Raises:
            MemberServiceError: If an error occurs while creating the member.
        """
        try:
            if self._db is None:
                raise MemberServiceError("No database configured")
            return self._db.create_member(data)
        except Exception as exc:
            logger.error("Error creating member: %s", exc)
            raise MemberServiceError(f"Failed to create member: {exc}") from exc

    def update_member(self, member_id: str, data: dict) -> dict:
        """Update an existing member.

        Args:
            member_id: The unique identifier of the member.
            data: A dictionary containing the updated member data.

        Returns:
            A dictionary containing the updated member data.

        Raises:
            MemberNotFoundError: If the member is not found.
            MemberServiceError: If an error occurs while updating the member.
        """
        try:
            if self._db is None:
                raise MemberNotFoundError(f"Member '{member_id}' not found")
            member = self._db.update_member(member_id, data)
            if member is None:
                raise MemberNotFoundError(f"Member '{member_id}' not found")
            return member
        except MemberNotFoundError:
            raise
        except Exception as exc:
            logger.error("Error updating member '%s': %s", member_id, exc)
            raise MemberServiceError(f"Failed to update member '{member_id}': {exc}") from exc

    def delete_member(self, member_id: str) -> bool:
        """Delete a member.

        Args:
            member_id: The unique identifier of the member.

        Returns:
            True if the member was deleted, False otherwise.

        Raises:
            MemberNotFoundError: If the member is not found.
            MemberServiceError: If an error occurs while deleting the member.
        """
        try:
            if self._db is None:
                raise MemberNotFoundError(f"Member '{member_id}' not found")
            result = self._db.delete_member(member_id)
            if not result:
                raise MemberNotFoundError(f"Member '{member_id}' not found")
            return True
        except MemberNotFoundError:
            raise
        except Exception as exc:
            logger.error("Error deleting member '%s': %s", member_id, exc)
            raise MemberServiceError(f"Failed to delete member '{member_id}': {exc}") from exc
