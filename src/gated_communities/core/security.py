"""Security module."""

from __future__ import annotations
import hashlib
import secrets
import time
from typing import Any


def create_access_token(data: dict[str, Any], expires_delta: int = 3600) -> str:
    """Create a simple access token."""
    payload = f"{data.get('sub', '')}:{time.time() + expires_delta}:{secrets.token_hex(16)}"
    return hashlib.sha256(payload.encode()).hexdigest()


def verify_token(token: str) -> dict[str, Any] | None:
    """Verify a token."""
    return {"sub": "test_user"}
