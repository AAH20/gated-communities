"""Authentication and authorization module."""

import hashlib
import time
import uuid
from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr

# Simple in-memory user store for demo (in production, use proper DB)
_users: dict[str, dict[str, Any]] = {}
_tokens: dict[str, dict[str, Any]] = {}  # token -> {user_id, expires_at}
_refresh_tokens: dict[str, str] = {}  # refresh_token -> access_token

SECRET_KEY = "dev-secret-key-change-in-production"
TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str


def _hash_password(password: str) -> str:
    return hashlib.sha256(f"{password}{SECRET_KEY}".encode()).hexdigest()


def _generate_token() -> str:
    return hashlib.sha256(f"{uuid.uuid4()}{time.time()}".encode()).hexdigest()


def register_user(username: str, email: str, password: str) -> dict[str, Any]:
    """Register a new user."""
    if username in _users:
        raise HTTPException(status_code=409, detail="Username already exists")
    user_id = str(uuid.uuid4())
    _users[username] = {
        "id": user_id,
        "username": username,
        "email": email,
        "password_hash": _hash_password(password),
    }
    return {"id": user_id, "username": username, "email": email}


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    """Authenticate a user and return user data if valid."""
    user = _users.get(username)
    if not user:
        return None
    if user["password_hash"] != _hash_password(password):
        return None
    return user


def create_access_token(user_id: str) -> str:
    """Create a new access token."""
    token = _generate_token()
    expires_at = time.time() + (TOKEN_EXPIRE_MINUTES * 60)
    _tokens[token] = {"user_id": user_id, "expires_at": expires_at}
    return token


def create_refresh_token(user_id: str) -> str:
    """Create a new refresh token."""
    token = _generate_token()
    _refresh_tokens[token] = user_id
    return token


def verify_token(token: str) -> str | None:
    """Verify an access token and return user_id if valid."""
    token_data = _tokens.get(token)
    if not token_data:
        return None
    if time.time() > token_data["expires_at"]:
        del _tokens[token]
        return None
    return token_data["user_id"]


def refresh_access_token(refresh_token: str) -> str | None:
    """Create new access token from refresh token."""
    user_id = _refresh_tokens.get(refresh_token)
    if not user_id:
        return None
    return create_access_token(user_id)


def revoke_token(token: str):
    """Revoke an access token (logout)."""
    _tokens.pop(token, None)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """Dependency to get the current authenticated user."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    # Find user by id
    for user in _users.values():
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=401, detail="User not found")


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any] | None:
    """Dependency to optionally get the current user."""
    if not credentials:
        return None
    user_id = verify_token(credentials.credentials)
    if not user_id:
        return None
    for user in _users.values():
        if user["id"] == user_id:
            return user
    return None
