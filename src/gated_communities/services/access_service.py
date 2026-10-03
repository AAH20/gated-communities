"""Access control service for gated communities.

Provides functions to check, grant, revoke, and retrieve access permissions
for members on community resources.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# In-memory store: {(member_id, resource): set(permissions)}
_access_store: dict[tuple[str, str], set[str]] = {}


def check_access(member_id: str, resource: str) -> dict:
    """Check whether a member has access to a resource.

    Args:
        member_id: Unique identifier of the member.
        resource: Identifier of the resource to check access for.

    Returns:
        A dictionary with keys:
            - ``has_access`` (bool): True if the member has any permissions.
            - ``permissions`` (list[str]): Sorted list of granted permissions.

    Raises:
        ValueError: If ``member_id`` or ``resource`` is empty or None.
    """
    if not member_id:
        raise ValueError("member_id must be a non-empty string")
    if not resource:
        raise ValueError("resource must be a non-empty string")

    permissions = _access_store.get((member_id, resource), set())
    return {
        "has_access": len(permissions) > 0,
        "permissions": sorted(permissions),
    }


def grant_access(member_id: str, resource: str, permissions: list[str]) -> bool:
    """Grant access permissions to a member for a resource.

    If the member already has some permissions, the new permissions are
    merged with the existing ones.

    Args:
        member_id: Unique identifier of the member.
        resource: Identifier of the resource to grant access to.
        permissions: List of permission strings to grant.

    Returns:
        True if access was granted successfully.

    Raises:
        ValueError: If ``member_id`` or ``resource`` is empty, or if
            ``permissions`` is not a list of strings.
    """
    if not member_id:
        raise ValueError("member_id must be a non-empty string")
    if not resource:
        raise ValueError("resource must be a non-empty string")
    if not isinstance(permissions, list) or not all(isinstance(p, str) for p in permissions):
        raise ValueError("permissions must be a list of strings")

    key = (member_id, resource)
    if key not in _access_store:
        _access_store[key] = set()

    _access_store[key].update(permissions)
    logger.info(
        "Granted access: member=%s resource=%s permissions=%s",
        member_id,
        resource,
        permissions,
    )
    return True


def revoke_access(member_id: str, resource: str) -> bool:
    """Revoke all access permissions for a member on a resource.

    Args:
        member_id: Unique identifier of the member.
        resource: Identifier of the resource to revoke access from.

    Returns:
        True if access was revoked (or was already absent), False otherwise.

    Raises:
        ValueError: If ``member_id`` or ``resource`` is empty or None.
    """
    if not member_id:
        raise ValueError("member_id must be a non-empty string")
    if not resource:
        raise ValueError("resource must be a non-empty string")

    key = (member_id, resource)
    if key in _access_store:
        del _access_store[key]
        logger.info("Revoked access: member=%s resource=%s", member_id, resource)
        return True

    logger.info("No access to revoke: member=%s resource=%s", member_id, resource)
    return True


def get_access_permissions(member_id: str, resource: str) -> list[str]:
    """Get the list of access permissions for a member on a resource.

    Args:
        member_id: Unique identifier of the member.
        resource: Identifier of the resource.

    Returns:
        Sorted list of permission strings. Returns an empty list if the
        member has no permissions on the resource.

    Raises:
        ValueError: If ``member_id`` or ``resource`` is empty or None.
    """
    if not member_id:
        raise ValueError("member_id must be a non-empty string")
    if not resource:
        raise ValueError("resource must be a non-empty string")

    permissions = _access_store.get((member_id, resource), set())
    return sorted(permissions)
