"""Post service for gated communities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol


class PostNotFoundError(Exception):
    """Raised when a post cannot be found."""


class CommunityNotFoundError(Exception):
    """Raised when a community cannot be found."""


class ValidationError(Exception):
    """Raised when post data fails validation."""


class RepositoryError(Exception):
    """Raised when a repository operation fails."""


@dataclass(frozen=True)
class Pagination:
    """Pagination parameters."""

    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValidationError("page must be >= 1")
        if self.page_size < 1 or self.page_size > 100:
            raise ValidationError("page_size must be between 1 and 100")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


@dataclass
class Post:
    """Domain model for a post."""

    id: str
    community_id: str
    author_id: str
    title: str
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_pinned: bool = False
    is_locked: bool = False
    tags: list[str] = field(default_factory=list)


class PostRepository(Protocol):
    """Protocol for post persistence."""

    async def create(self, post: Post) -> Post: ...

    async def get_by_id(self, post_id: str) -> Post | None: ...

    async def list_by_community(self, community_id: str, offset: int, limit: int) -> list[Post]: ...

    async def count_by_community(self, community_id: str) -> int: ...

    async def update(self, post: Post) -> Post: ...

    async def delete(self, post_id: str) -> bool: ...


class CommunityRepository(Protocol):
    """Protocol for community lookups."""

    async def exists(self, community_id: str) -> bool: ...


def _validate_post_data(data: dict[str, Any]) -> None:
    """Validate raw post data before creation."""
    required_fields = ("community_id", "author_id", "title", "content")
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    title = data["title"]
    if not isinstance(title, str) or not title.strip():
        raise ValidationError("title must be a non-empty string")
    if len(title) > 200:
        raise ValidationError("title must be 200 characters or fewer")

    content = data["content"]
    if not isinstance(content, str) or not content.strip():
        raise ValidationError("content must be a non-empty string")
    if len(content) > 50_000:
        raise ValidationError("content must be 50,000 characters or fewer")

    community_id = data["community_id"]
    if not isinstance(community_id, str) or not community_id.strip():
        raise ValidationError("community_id must be a non-empty string")

    author_id = data["author_id"]
    if not isinstance(author_id, str) or not author_id.strip():
        raise ValidationError("author_id must be a non-empty string")

    tags = data.get("tags", [])
    if not isinstance(tags, list):
        raise ValidationError("tags must be a list")
    if len(tags) > 10:
        raise ValidationError("tags must contain at most 10 items")
    for tag in tags:
        if not isinstance(tag, str) or not tag.strip():
            raise ValidationError("each tag must be a non-empty string")


class PostService:
    """Service for post operations in gated communities."""

    def __init__(
        self,
        post_repo: PostRepository,
        community_repo: CommunityRepository,
    ) -> None:
        self._post_repo = post_repo
        self._community_repo = community_repo

    async def create_post(self, data: dict[str, Any]) -> Post:
        """Create a new post with validation.

        Args:
            data: Dictionary containing post fields.

        Returns:
            The created Post.

        Raises:
            ValidationError: If data fails validation.
            CommunityNotFoundError: If the community does not exist.
            RepositoryError: If persistence fails.
        """
        _validate_post_data(data)

        community_id = data["community_id"]
        if not await self._community_repo.exists(community_id):
            raise CommunityNotFoundError(f"Community '{community_id}' not found")

        post = Post(
            id="",
            community_id=community_id,
            author_id=data["author_id"],
            title=data["title"].strip(),
            content=data["content"].strip(),
            tags=[t.strip() for t in data.get("tags", [])],
        )

        try:
            return await self._post_repo.create(post)
        except Exception as exc:
            raise RepositoryError(f"Failed to create post: {exc}") from exc

    async def get_post(self, post_id: str) -> Post:
        """Get a post by its ID.

        Args:
            post_id: The unique post identifier.

        Returns:
            The matching Post.

        Raises:
            ValidationError: If post_id is empty.
            PostNotFoundError: If no post matches the ID.
            RepositoryError: If the lookup fails.
        """
        if not post_id or not post_id.strip():
            raise ValidationError("post_id must be a non-empty string")

        try:
            post = await self._post_repo.get_by_id(post_id)
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch post: {exc}") from exc

        if post is None:
            raise PostNotFoundError(f"Post '{post_id}' not found")

        return post

    async def list_posts(
        self,
        community_id: str,
        pagination: Pagination | None = None,
    ) -> tuple[list[Post], int]:
        """List posts in a community with pagination.

        Args:
            community_id: The community to list posts from.
            pagination: Pagination parameters (defaults to page 1, size 20).

        Returns:
            A tuple of (posts, total_count).

        Raises:
            ValidationError: If community_id is empty.
            CommunityNotFoundError: If the community does not exist.
            RepositoryError: If the query fails.
        """
        if not community_id or not community_id.strip():
            raise ValidationError("community_id must be a non-empty string")

        if not await self._community_repo.exists(community_id):
            raise CommunityNotFoundError(f"Community '{community_id}' not found")

        pag = pagination or Pagination()

        try:
            posts = await self._post_repo.list_by_community(community_id, pag.offset, pag.limit)
            total = await self._post_repo.count_by_community(community_id)
        except Exception as exc:
            raise RepositoryError(f"Failed to list posts: {exc}") from exc

        return posts, total

    async def update_post(self, post_id: str, data: dict[str, Any]) -> Post:
        """Update an existing post.

        Args:
            post_id: The unique identifier of the post to update.
            data: Dictionary containing the fields to update.

        Returns:
            The updated Post.

        Raises:
            ValidationError: If post_id is empty or data is empty.
            PostNotFoundError: If no post matches the ID.
            RepositoryError: If the update fails.
        """
        if not post_id or not post_id.strip():
            raise ValidationError("post_id must be a non-empty string")
        if not data:
            raise ValidationError("data must not be empty")

        try:
            post = await self._post_repo.get_by_id(post_id)
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch post: {exc}") from exc

        if post is None:
            raise PostNotFoundError(f"Post '{post_id}' not found")

        if "title" in data:
            title = data["title"]
            if not isinstance(title, str) or not title.strip():
                raise ValidationError("title must be a non-empty string")
            if len(title) > 200:
                raise ValidationError("title must be 200 characters or fewer")
            post.title = title.strip()

        if "content" in data:
            content = data["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValidationError("content must be a non-empty string")
            if len(content) > 50_000:
                raise ValidationError("content must be 50,000 characters or fewer")
            post.content = content.strip()

        if "tags" in data:
            tags = data["tags"]
            if not isinstance(tags, list):
                raise ValidationError("tags must be a list")
            if len(tags) > 10:
                raise ValidationError("tags must contain at most 10 items")
            for tag in tags:
                if not isinstance(tag, str) or not tag.strip():
                    raise ValidationError("each tag must be a non-empty string")
            post.tags = [t.strip() for t in tags]

        if "is_pinned" in data:
            post.is_pinned = bool(data["is_pinned"])

        if "is_locked" in data:
            post.is_locked = bool(data["is_locked"])

        post.updated_at = datetime.now(UTC)

        try:
            return await self._post_repo.update(post)
        except Exception as exc:
            raise RepositoryError(f"Failed to update post: {exc}") from exc

    async def delete_post(self, post_id: str) -> bool:
        """Delete a post by its ID.

        Args:
            post_id: The unique identifier of the post to delete.

        Returns:
            True if the post was deleted, False if it did not exist.

        Raises:
            ValidationError: If post_id is empty.
            RepositoryError: If the deletion fails.
        """
        if not post_id or not post_id.strip():
            raise ValidationError("post_id must be a non-empty string")

        try:
            return await self._post_repo.delete(post_id)
        except Exception as exc:
            raise RepositoryError(f"Failed to delete post: {exc}") from exc
