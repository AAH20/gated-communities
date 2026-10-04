"""SQL injection prevention tests for gated-communities."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gated_communities.main import app


class TestSQLInjectionPrevention:
    """Test that SQL injection attacks are prevented."""

    SQL_INJECTION_PAYLOADS = [
        "' OR '1'='1",
        "' OR 1=1--",
        "'; DROP TABLE users;--",
        "1' UNION SELECT * FROM users--",
        "' OR '1'='1' /*",
        "admin'--",
        "' OR 1=1#",
        "1 AND 1=1",
        "'; EXEC xp_cmdshell('dir');--",
        "' OR ''='",
        "1; SELECT * FROM users",
        "' UNION SELECT null, null, null--",
        "1' AND (SELECT COUNT(*) FROM users) > 0--",
        "'; INSERT INTO users VALUES ('hacker', 'pass')--",
        "' OR 1=1 LIMIT 1--",
        "1' OR '1'='1",
        "'; UPDATE users SET password='hacked'--",
        "' OR 'x'='x",
        "1 AND 1=2",
        "'; DELETE FROM users WHERE '1'='1",
    ]

    @pytest.fixture
    def client(self):
        with TestClient(app) as c:
            yield c

    def test_login_sql_injection_username(self, client):
        """Test that SQL injection in login username is prevented."""
        for payload in self.SQL_INJECTION_PAYLOADS:
            resp = client.post(
                "/auth/login",
                json={"username": payload, "password": "test123"}
            )
            assert resp.status_code != 200, (
                f"SQL injection succeeded with payload: {payload}"
            )

    def test_login_sql_injection_password(self, client):
        """Test that SQL injection in login password is prevented."""
        for payload in self.SQL_INJECTION_PAYLOADS:
            resp = client.post(
                "/auth/login",
                json={"username": "testuser", "password": payload}
            )
            assert resp.status_code != 200, (
                f"SQL injection succeeded with payload: {payload}"
            )

    def test_register_sql_injection_username(self, client):
        """Test that SQL injection in register username is prevented."""
        for payload in self.SQL_INJECTION_PAYLOADS:
            resp = client.post(
                "/auth/register",
                json={
                    "username": payload,
                    "email": f"test_{hash(payload)}@example.com",
                    "password": "test123"
                }
            )
            # Should not create a user with SQL injection payload
            if resp.status_code == 201:
                data = resp.json()
                assert "OR" not in data.get("username", ""), (
                    f"SQL injection in username not sanitized: {payload}"
                )

    def test_community_id_sql_injection(self, client):
        """Test SQL injection in community ID path parameter."""
        # First create a user and get token
        from gated_communities.auth import register_user, create_access_token
        register_user("sqltest", "sqltest@example.com", "testpass123")
        token = create_access_token("sqltest")

        for payload in self.SQL_INJECTION_PAYLOADS:
            resp = client.get(
                f"/communities/{payload}",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert resp.status_code != 500, (
                f"SQL injection caused server error with payload: {payload}"
            )

    def test_member_id_sql_injection(self, client):
        """Test SQL injection in member ID path parameter."""
        from gated_communities.auth import register_user, create_access_token
        register_user("sqltest2", "sqltest2@example.com", "testpass123")
        token = create_access_token("sqltest2")

        for payload in self.SQL_INJECTION_PAYLOADS:
            resp = client.get(
                f"/members/{payload}",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert resp.status_code != 500, (
                f"SQL injection caused server error with payload: {payload}"
            )
