"""Input validation tests for gated-communities."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gated_communities.main import app


class TestInputValidation:
    """Test that input validation is properly enforced."""

    @pytest.fixture
    def client(self):
        with TestClient(app) as c:
            yield c

    def test_register_username_required(self, client):
        """Test that username is required for registration."""
        resp = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "test123"
            }
        )
        assert resp.status_code == 422, "Registration without username was accepted"

    def test_register_email_required(self, client):
        """Test that email is required for registration."""
        resp = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "password": "test123"
            }
        )
        assert resp.status_code == 422, "Registration without email was accepted"

    def test_register_password_minimum_length(self, client):
        """Test that password meets minimum length."""
        resp = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "short"
            }
        )
        assert resp.status_code == 422, "Short password was accepted"

    def test_register_email_format(self, client):
        """Test that email format is validated."""
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
        ]
        for email in invalid_emails:
            resp = client.post(
                "/auth/register",
                json={
                    "username": f"test_{hash(email)}",
                    "email": email,
                    "password": "test123"
                }
            )
            assert resp.status_code == 422, (
                f"Invalid email '{email}' was accepted"
            )

    def test_login_username_required(self, client):
        """Test that username is required for login."""
        resp = client.post(
            "/auth/login",
            json={"password": "test123"}
        )
        assert resp.status_code == 422, "Login without username was accepted"

    def test_login_password_required(self, client):
        """Test that password is required for login."""
        resp = client.post(
            "/auth/login",
            json={"username": "testuser"}
        )
        assert resp.status_code == 422, "Login without password was accepted"

    def test_community_name_required(self, client):
        """Test that community name is required."""
        from gated_communities.auth import register_user, create_access_token
        register_user("validationtest", "validation@example.com", "testpass123")
        token = create_access_token("validationtest")

        resp = client.post(
            "/communities",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "description": "Test",
                "is_private": False,
                "tier_id": "free",
                "capacity": 100
            }
        )
        assert resp.status_code == 422, "Community without name was accepted"

    def test_community_capacity_validation(self, client):
        """Test that community capacity is validated."""
        from gated_communities.auth import register_user, create_access_token
        register_user("validationtest2", "validation2@example.com", "testpass123")
        token = create_access_token("validationtest2")

        resp = client.post(
            "/communities",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Test Community",
                "description": "Test",
                "is_private": False,
                "tier_id": "free",
                "capacity": -1
            }
        )
        # Should validate capacity is positive
        assert resp.status_code in (422, 400), "Negative capacity was accepted"

    def test_null_byte_in_input(self, client):
        """Test that null bytes in input are handled."""
        resp = client.post(
            "/auth/register",
            json={
                "username": "test\x00user",
                "email": "test@example.com",
                "password": "test123"
            }
        )
        assert resp.status_code != 500, "Null byte caused server error"

    def test_very_long_input(self, client):
        """Test that very long input is handled gracefully."""
        long_string = "a" * 100000
        resp = client.post(
            "/auth/register",
            json={
                "username": long_string,
                "email": "test@example.com",
                "password": "test123"
            }
        )
        assert resp.status_code != 500, "Very long input caused server error"

    def test_special_characters_in_input(self, client):
        """Test that special characters in input are handled."""
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        resp = client.post(
            "/auth/register",
            json={
                "username": f"Test{special_chars}User",
                "email": "test@example.com",
                "password": "test123"
            }
        )
        assert resp.status_code != 500, "Special characters caused server error"

    def test_password_change_validation(self, client):
        """Test that password change validates input."""
        from gated_communities.auth import register_user, create_access_token
        register_user("pwdchange", "pwdchange@example.com", "testpass123")
        token = create_access_token("pwdchange")

        # Try to change to a short password
        resp = client.post(
            "/auth/password/change",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "testpass123",
                "new_password": "short"
            }
        )
        assert resp.status_code == 422, "Short new password was accepted"
