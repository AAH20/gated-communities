"""Access control functions."""

from __future__ import annotations
from enum import StrEnum


class AccessLevel(StrEnum):
    """Access level enumeration."""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class AccessDeniedError(Exception):
    """Raised when access is denied."""
    pass


class AccessAlreadyGrantedError(Exception):
    """Raised when access is already granted."""
    pass


class AccessNotFoundError(Exception):
    """Raised when access is not found."""
    pass


_access_store: dict[tuple[str, str], set[str]] = {}


def check_access(member_id: str, resource: str) -> dict:
    """Check whether a member has access to a resource."""
    perms = _access_store.get((member_id, resource), set())
    return {"has_access": bool(perms), "permissions": sorted(perms)}


def grant_access(member_id: str, resource: str, permissions: list[str]) -> dict:
    """Grant access to a member."""
    key = (member_id, resource)
    if key in _access_store:
        raise AccessAlreadyGrantedError(f"Access already granted for {member_id} on {resource}")
    _access_store[key] = set(permissions)
    return {"member_id": member_id, "resource": resource, "permissions": permissions}


def revoke_access(member_id: str, resource: str) -> dict:
    """Revoke access from a member."""
    key = (member_id, resource)
    if key not in _access_store:
        raise AccessNotFoundError(f"No access found for {member_id} on {resource}")
    del _access_store[key]
    return {"member_id": member_id, "resource": resource, "revoked": True}


def get_access_permissions(member_id: str, resource: str) -> list[str]:
    """Get access permissions for a member on a resource."""
    return sorted(_access_store.get((member_id, resource), set()))
