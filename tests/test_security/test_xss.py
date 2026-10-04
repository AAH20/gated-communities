"""XSS prevention tests for gated-communities."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gated_communities.main import app
from gated_communities.middleware.sanitize import sanitize_string


class TestXSSPrevention:
    """Test that XSS attacks are prevented."""

    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<body onload=alert('XSS')>",
        "<iframe src='javascript:alert(1)'>",
        "<input onfocus=alert('XSS') autofocus>",
        "<marquee onstart=alert('XSS')>",
        "<details open ontoggle=alert('XSS')>",
        "\"><script>alert('XSS')</script>",
        "'><script>alert('XSS')</script>",
        "<img src=\"javascript:alert('XSS')\">",
        "<a href=\"javascript:alert('XSS')\">click</a>",
        "<div style=\"background-image: url(javascript:alert('XSS'))\">",
        "<object data=\"javascript:alert('XSS')\">",
        "<embed src=\"javascript:alert('XSS')\">",
        "<form><button formaction=\"javascript:alert('XSS')\">",
        "<video><source onerror=\"alert('XSS')\">",
        "<audio src=x onerror=alert('XSS')>",
    ]

    @pytest.fixture
    def client(self):
        with TestClient(app) as c:
            yield c

    def test_sanitize_string_escapes_html(self):
        """Test that sanitize_string properly escapes HTML."""
        for payload in self.XSS_PAYLOADS:
            sanitized = sanitize_string(payload)
            assert "<script>" not in sanitized.lower(), (
                f"XSS payload not sanitized: {payload} -> {sanitized}"
            )

    def test_sanitize_string_removes_null_bytes(self):
        """Test that sanitize_string removes null bytes."""
        result = sanitize_string("test\x00input")
        assert "\x00" not in result

    def test_sanitize_string_removes_control_chars(self):
        """Test that sanitize_string removes control characters."""
        result = sanitize_string("test\x01\x02input")
        assert "\x01" not in result
        assert "\x02" not in result

    def test_register_xss_in_username(self, client):
        """Test that XSS in registration username is sanitized."""
        for payload in self.XSS_PAYLOADS:
            resp = client.post(
                "/auth/register",
                json={
                    "username": payload,
                    "email": f"xss_test_{hash(payload)}@example.com",
                    "password": "test123"
                }
            )
            if resp.status_code == 201:
                data = resp.json()
                username = data.get("username", "")
                assert "<script>" not in username.lower(), (
                    f"XSS payload stored unsanitized: {payload}"
                )

    def test_community_create_xss_in_name(self, client):
        """Test that XSS in community name is sanitized."""
        from gated_communities.auth import register_user, create_access_token
        register_user("xsstest", "xsstest@example.com", "testpass123")
        token = create_access_token("xsstest")

        for payload in self.XSS_PAYLOADS:
            resp = client.post(
                "/communities",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": payload,
                    "description": "Test community",
                    "is_private": False,
                    "tier_id": "free",
                    "capacity": 100
                }
            )
            if resp.status_code == 201:
                data = resp.json()
                name = data.get("name", "")
                assert "<script>" not in name.lower(), (
                    f"XSS payload stored unsanitized in community name: {payload}"
                )

    def test_community_create_xss_in_description(self, client):
        """Test that XSS in community description is sanitized."""
        from gated_communities.auth import register_user, create_access_token
        register_user("xsstest2", "xsstest2@example.com", "testpass123")
        token = create_access_token("xsstest2")

        for payload in self.XSS_PAYLOADS:
            resp = client.post(
                "/communities",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": "Test Community",
                    "description": payload,
                    "is_private": False,
                    "tier_id": "free",
                    "capacity": 100
                }
            )
            if resp.status_code == 201:
                data = resp.json()
                description = data.get("description", "")
                assert "<script>" not in description.lower(), (
                    f"XSS payload stored unsanitized in description: {payload}"
                )
