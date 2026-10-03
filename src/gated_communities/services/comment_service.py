"""Comment service for gated communities."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


class CommentServiceError(Exception):
    """Base exception for comment service errors."""


class CommentNotFoundError(CommentServiceError):
    """Raised when a comment cannot be found."""


class CommentValidationError(CommentServiceError):
    """Raised when comment data fails validation."""


class CommentService:
    """Service for managing comments on gated community posts."""

    def __init__(self) -> None:
        """Initialize the comment service with an in-memory store."""
        self._comments: dict[str, dict[str, Any]] = {}

    def get_comment(self, comment_id: str) -> dict:
        """Get a comment by its ID.

        Args:
            comment_id: The unique identifier of the comment.

        Returns:
            The comment data as a dictionary.

        Raises:
            CommentNotFoundError: If no comment exists with the given ID.
            CommentValidationError: If comment_id is empty or invalid.
        """
        if not comment_id or not isinstance(comment_id, str):
            raise CommentValidationError("comment_id must be a non-empty string")

        comment = self._comments.get(comment_id)
        if comment is None:
            raise CommentNotFoundError(f"Comment with id '{comment_id}' not found")

        return dict(comment)

    def list_comments(self, filters: dict, page: int, page_size: int) -> list[dict]:
        """List comments with optional filtering and pagination.

        Args:
            filters: Dictionary of filter criteria (e.g., post_id, author_id).
            page: Page number (1-indexed).
            page_size: Number of comments per page.

        Returns:
            A list of comment dictionaries matching the filters.

        Raises:
            CommentValidationError: If page or page_size is invalid.
        """
        if page < 1:
            raise CommentValidationError("page must be >= 1")
        if page_size < 1:
            raise CommentValidationError("page_size must be >= 1")

        filtered = list(self._comments.values())

        if filters:
            filtered = [c for c in filtered if all(c.get(k) == v for k, v in filters.items())]

        start = (page - 1) * page_size
        end = start + page_size

        return [dict(c) for c in filtered[start:end]]

    def create_comment(self, data: dict) -> dict:
        """Create a new comment with validation.

        Args:
            data: Dictionary containing comment data. Required keys:
                - post_id: ID of the post being commented on
                - author_id: ID of the comment author
                - content: Comment text content

        Returns:
            The created comment data as a dictionary.

        Raises:
            CommentValidationError: If required fields are missing or invalid.
        """
        if not isinstance(data, dict):
            raise CommentValidationError("data must be a dictionary")

        required_fields = ["post_id", "author_id", "content"]
        missing = [f for f in required_fields if f not in data or data[f] is None]
        if missing:
            raise CommentValidationError(f"Missing required fields: {', '.join(missing)}")

        content = str(data["content"]).strip()
        if not content:
            raise CommentValidationError("Comment content cannot be empty")

        if len(content) > 10000:
            raise CommentValidationError(
                "Comment content exceeds maximum length of 10000 characters"
            )

        comment_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        comment = {
            "id": comment_id,
            "post_id": str(data["post_id"]),
            "author_id": str(data["author_id"]),
            "content": content,
            "created_at": now,
            "updated_at": now,
            "parent_id": str(data["parent_id"]) if data.get("parent_id") else None,
            "is_edited": False,
            "is_deleted": False,
        }

        self._comments[comment_id] = comment
        return dict(comment)

    def update_comment(self, comment_id: str, data: dict) -> dict:
        """Update an existing comment.

        Args:
            comment_id: The unique identifier of the comment to update.
            data: Dictionary containing fields to update.

        Returns:
            The updated comment data as a dictionary.

        Raises:
            CommentNotFoundError: If the comment does not exist.
            CommentValidationError: If comment_id is empty or data is invalid.
        """
        if not comment_id or not isinstance(comment_id, str):
            raise CommentValidationError("comment_id must be a non-empty string")
        if not isinstance(data, dict):
            raise CommentValidationError("data must be a dictionary")

        comment = self._comments.get(comment_id)
        if comment is None:
            raise CommentNotFoundError(f"Comment with id '{comment_id}' not found")

        protected = {"id", "created_at"}
        for key, value in data.items():
            if key not in protected:
                comment[key] = value

        comment["updated_at"] = datetime.now(UTC).isoformat()
        comment["is_edited"] = True
        return dict(comment)

    def delete_comment(self, comment_id: str) -> bool:
        """Delete a comment by its ID.

        Args:
            comment_id: The unique identifier of the comment to delete.

        Returns:
            True if the comment was deleted, False if it did not exist.

        Raises:
            CommentValidationError: If comment_id is empty or invalid.
        """
        if not comment_id or not isinstance(comment_id, str):
            raise CommentValidationError("comment_id must be a non-empty string")

        if comment_id not in self._comments:
            return False

        del self._comments[comment_id]
        return True
