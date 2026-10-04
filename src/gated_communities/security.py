"""Security module for role-based access control and authorization.

This module provides dependencies and utilities for enforcing role-based
access control (RBAC) across all API endpoints.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Member, MemberRole


# Role hierarchy: higher roles inherit permissions from lower roles
ROLE_HIERARCHY: dict[str, set[str]] = {
    "owner": {"owner", "admin", "moderator", "member"},
    "admin": {"admin", "moderator", "member"},
    "moderator": {"moderator", "member"},
    "member": {"member"},
}


def _role_at_least(user_role: str, required_role: str) -> bool:
    """Check if user_role has at least the permissions of required_role."""
    return required_role in ROLE_HIERARCHY.get(user_role, set())


def get_user_role_in_community(
    user_id: str | int,
    community_id: int,
    db: Session,
) -> MemberRole | None:
    """Get a user's role in a specific community.

    Returns None if the user is not a member of the community.
    """
    # Handle both string UUID and integer user IDs
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        # If user_id is a UUID string, we can't match against integer Member.user_id
        # In a production system, these would be the same type
        return None

    membership = (
        db.query(Member)
        .filter(
            Member.community_id == community_id,
            Member.user_id == user_id_int,
        )
        .first()
    )
    return membership.role if membership else None


def require_auth(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Require an authenticated user.

    This is a simple wrapper around get_current_user that provides
    a consistent interface for authentication requirements.
    """
    return current_user


def require_role(
    allowed_roles: list[str],
) -> Callable:
    """Create a dependency that requires the user to have one of the allowed roles.

    This checks the user's role across all communities. For community-specific
    role checks, use require_community_role.

    Args:
        allowed_roles: List of role names that are permitted (e.g., ["admin", "moderator"])

    Returns:
        A FastAPI dependency that enforces the role requirement.
    """
    def role_checker(
        current_user: dict[str, Any] = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        # Check if user has the required role in any community
        try:
            user_id_int = int(current_user["id"])
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
            )

        user_memberships = db.query(Member).filter(Member.user_id == user_id_int).all()
        user_roles = {m.role.value for m in user_memberships}

        if not any(role in allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


def require_community_role(
    community_id: int,
    allowed_roles: list[str],
) -> Callable:
    """Create a dependency that requires a specific role in a community.

    Args:
        community_id: The ID of the community to check membership in
        allowed_roles: List of role names that are permitted

    Returns:
        A FastAPI dependency that enforces the community role requirement.
    """
    def role_checker(
        current_user: dict[str, Any] = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        user_role = get_user_role_in_community(
            current_user["id"], community_id, db
        )
        if user_role is None or user_role.value not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


def require_community_role_or_owner(
    community_id: int,
) -> Callable:
    """Require the user to be an owner or admin of the community."""
    return require_community_role(community_id, ["owner", "admin"])


def require_moderator(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Require the user to be a moderator or higher in any community."""
    try:
        user_id_int = int(current_user["id"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions",
        )

    user_memberships = db.query(Member).filter(Member.user_id == user_id_int).all()
    user_roles = {m.role.value for m in user_memberships}

    if not any(r in ("owner", "admin", "moderator") for r in user_roles):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions",
        )
    return current_user


def sanitize_error_detail(detail: str) -> str:
    """Sanitize error details to prevent information disclosure.

    Returns a generic message for sensitive errors to avoid leaking
    internal implementation details.
    """
    sensitive_patterns = [
        "sql",
        "database",
        "query",
        "table",
        "column",
        "schema",
        "password",
        "secret",
        "token",
        "key",
    ]
    detail_lower = detail.lower()
    if any(pattern in detail_lower for pattern in sensitive_patterns):
        return "An error occurred"
    return detail
