"""Access control agent for gated communities.

Provides functions to check, grant, and revoke member access to resources.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# In-memory access store: {member_id: {resource: set(permissions)}}
_access_store: dict[str, dict[str, set[str]]] = {}


def check_access(member_id: str, resource: str) -> dict[str, Any]:
    """Check a member's access to a resource.

    Args:
        member_id: Unique identifier of the member.
        resource: The resource to check access for.

    Returns:
        A dictionary with keys:
            - 'member_id': The member's ID.
            - 'resource': The resource name.
            - 'has_access': Boolean indicating whether access is granted.
            - 'permissions': List of permission strings (empty if no access).

    Raises:
        ValueError: If member_id or resource is empty or not a string.
    """
    if not isinstance(member_id, str) or not member_id.strip():
        raise ValueError("member_id must be a non-empty string")
    if not isinstance(resource, str) or not resource.strip():
        raise ValueError("resource must be a non-empty string")

    member_perms = _access_store.get(member_id, {})
    permissions = member_perms.get(resource, set())

    return {
        "member_id": member_id,
        "resource": resource,
        "has_access": len(permissions) > 0,
        "permissions": sorted(permissions),
    }


def grant_access(member_id: str, resource: str, permissions: list[str]) -> bool:
    """Grant a member access to a resource with specified permissions.

    Args:
        member_id: Unique identifier of the member.
        resource: The resource to grant access to.
        permissions: List of permission strings to grant.

    Returns:
        True if access was granted successfully.

    Raises:
        ValueError: If member_id or resource is empty, or if permissions
            is not a list of non-empty strings.
    """
    if not isinstance(member_id, str) or not member_id.strip():
        raise ValueError("member_id must be a non-empty string")
    if not isinstance(resource, str) or not resource.strip():
        raise ValueError("resource must be a non-empty string")
    if not isinstance(permissions, list):
        raise ValueError("permissions must be a list of strings")
    for perm in permissions:
        if not isinstance(perm, str) or not perm.strip():
            raise ValueError("each permission must be a non-empty string")

    if member_id not in _access_store:
        _access_store[member_id] = {}
    if resource not in _access_store[member_id]:
        _access_store[member_id][resource] = set()

    _access_store[member_id][resource].update(permissions)
    logger.info("Granted %s access to %s with permissions %s", member_id, resource, permissions)
    return True


def revoke_access(member_id: str, resource: str) -> bool:
    """Revoke a member's access to a resource.

    Args:
        member_id: Unique identifier of the member.
        resource: The resource to revoke access from.

    Returns:
        True if access was revoked (or was already absent), False otherwise.

    Raises:
        ValueError: If member_id or resource is empty or not a string.
    """
    if not isinstance(member_id, str) or not member_id.strip():
        raise ValueError("member_id must be a non-empty string")
    if not isinstance(resource, str) or not resource.strip():
        raise ValueError("resource must be a non-empty string")

    if member_id in _access_store and resource in _access_store[member_id]:
        del _access_store[member_id][resource]
        # Clean up empty member entries
        if not _access_store[member_id]:
            del _access_store[member_id]
        logger.info("Revoked %s access to %s", member_id, resource)
        return True

    logger.info("No access to revoke for %s on %s", member_id, resource)
    return True
