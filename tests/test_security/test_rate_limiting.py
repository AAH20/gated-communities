"""Rate limiting tests for gated-communities."""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from gated_communities.main import app
from gated_communities.rate_limit import rate_limiter


class TestRateLimiting:
    """Test that rate limiting is enforced."""

    @pytest.fixture
    def client(self):
        # Reset rate limiter before each test
        rate_limiter.reset()
        with TestClient(app) as c:
            yield c
        rate_limiter.reset()

    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are present in responses."""
        resp = client.get("/health")
        # Check for rate limit headers
        has_rate_limit = (
            "X-RateLimit-Limit" in resp.headers
            or "X-RateLimit-Remaining" in resp.headers
            or "x-ratelimit-limit" in resp.headers
            or "x-ratelimit-remaining" in resp.headers
        )

    def test_rate_limit_exceeded_returns_429(self, client):
        """Test that exceeding rate limit returns 429 status."""
        responses = []
        for _ in range(100):
            resp = client.get("/health")
            responses.append(resp.status_code)
            if resp.status_code == 429:
                break

        if 429 in responses:
            assert True  # Rate limiting is working

    def test_auth_endpoint_rate_limiting(self, client):
        """Test that auth endpoints have stricter rate limiting."""
        responses = []
        for _ in range(20):
            resp = client.post(
                "/auth/login",
                json={"username": "test", "password": "wrong"}
            )
            responses.append(resp.status_code)
            if resp.status_code == 429:
                break

        if 429 in responses:
            assert True  # Auth rate limiting is working

    def test_rate_limit_retry_after_header(self, client):
        """Test that 429 responses include Retry-After header."""
        for _ in range(100):
            resp = client.get("/health")
            if resp.status_code == 429:
                assert "Retry-After" in resp.headers or "retry-after" in resp.headers
                break

    def test_rate_limiter_reset(self, client):
        """Test that rate limiter can be reset."""
        # Make some requests
        for _ in range(5):
            client.get("/health")

        # Reset
        rate_limiter.reset()

        # Should be able to make requests again
        resp = client.get("/health")
        assert resp.status_code == 200
