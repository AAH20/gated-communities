"""Local fixtures shared by the ``tests/test_api`` suite.

Why this file exists
--------------------
``tests/conftest.py``'s ``auth_headers`` fixture re-registers the fixed
username ``testuser`` for every test.  The auth layer keeps users in a
module-level dict that outlives the per-test database reset, so the *second*
test in a run receives ``409 Registration failed``.  This override registers a
uniquely-named user per test via the real ``/auth/register`` + ``/auth/login``
endpoints, which is also a more faithful exercise of the shipped API.
"""

from __future__ import annotations

import uuid

import pytest


@pytest.fixture
def auth_headers(client):
    """Register a fresh user and return ``{"Authorization": "Bearer <token>"}``."""
    username = f"user_{uuid.uuid4().hex[:12]}"
    email = f"{username}@example.com"
    password = "testpass123"

    resp = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert resp.status_code == 201, resp.text

    login = client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}
