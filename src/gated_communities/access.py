"""Access control module."""

from __future__ import annotations
from enum import StrEnum
from typing import Any


class AccessDecision(StrEnum):
    """Access decision enumeration."""
    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"


class AccessRequest:
    """Access request model."""
    def __init__(self, member_id: str, resource: str, action: str = "read", **kwargs):
        self.member_id = member_id
        self.resource = resource
        self.action = action
        self.context = kwargs


class AccessController:
    """Access controller."""
    def check_access(self, request: AccessRequest) -> AccessDecision:
        return AccessDecision.GRANTED
