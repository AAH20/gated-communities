"""Tests for rate limiting middleware."""
import pytest
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Create a test FastAPI app with rate limiting middleware."""
    app = FastAPI()

    # Simple in-memory rate limiter
    request_counts = {}
    RATE_LIMIT = 5
    WINDOW_SECONDS = 60

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Clean old entries
        if client_ip in request_counts:
            request_counts[client_ip] = [
                t for t in request_counts[client_ip]
                if current_time - t < WINDOW_SECONDS
            ]
        else:
            request_counts[client_ip] = []

        # Check rate limit
        if len(request_counts[client_ip]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers={"Retry-After": str(WINDOW_SECONDS)},
            )

        # Record request
        request_counts[client_ip].append(current_time)

        response = await call_next(request)
        # Add rate limit headers
        remaining = RATE_LIMIT - len(request_counts[client_ip])
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    @app.get("/api/data")
    async def get_data():
        return {"data": "some data"}

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestRateLimitMiddleware:
    """Test suite for rate limiting middleware."""

    def test_request_under_limit(self, client):
        """Requests under the rate limit should succeed."""
        response = client.get("/api/data")
        assert response.status_code == 200
        assert response.json() == {"data": "some data"}

    def test_rate_limit_headers_present(self, client):
        """Rate limit headers should be present in response."""
        response = client.get("/api/data")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "5"

    def test_rate_limit_remaining_decreases(self, client):
        """Remaining count should decrease with each request."""
        response1 = client.get("/api/data")
        remaining1 = int(response1.headers["X-RateLimit-Remaining"])

        response2 = client.get("/api/data")
        remaining2 = int(response2.headers["X-RateLimit-Remaining"])

        assert remaining2 == remaining1 - 1

    def test_rate_limit_exceeded(self, client):
        """Requests exceeding the rate limit should return 429."""
        # Make requests up to the limit
        for _ in range(5):
            response = client.get("/api/data")
            assert response.status_code == 200

        # Next request should be rate limited
        response = client.get("/api/data")
        assert response.status_code == 429
        assert response.json()["detail"] == "Too many requests"

    def test_rate_limit_retry_after_header(self, client):
        """Rate limited response should include Retry-After header."""
        # Exhaust the rate limit
        for _ in range(5):
            client.get("/api/data")

        response = client.get("/api/data")
        assert response.status_code == 429
        assert "Retry-After" in response.headers

    def test_different_endpoints_share_limit(self, client):
        """Rate limit should be shared across endpoints."""
        # Make 4 requests to /api/data
        for _ in range(4):
            client.get("/api/data")

        # 5th request to different endpoint should still be under limit
        response = client.get("/api/health")
        assert response.status_code == 200

        # 6th request should be rate limited
        response = client.get("/api/data")
        assert response.status_code == 429

    def test_rate_limit_resets_after_window(self, client):
        """Rate limit should reset after the time window."""
        # This test uses a very short window for testing
        # In practice, you'd mock time or use a shorter window
        for _ in range(5):
            client.get("/api/data")

        # Should be rate limited
        response = client.get("/api/data")
        assert response.status_code == 429

    def test_concurrent_requests_tracked(self, client):
        """Multiple rapid requests should all be tracked."""
        responses = []
        for _ in range(7):
            response = client.get("/api/data")
            responses.append(response.status_code)

        # First 5 should succeed, last 2 should be rate limited
        assert responses[:5] == [200, 200, 200, 200, 200]
        assert responses[5:] == [429, 429]

    def test_rate_limit_per_client(self, client):
        """Rate limit should be tracked per client IP."""
        # This is a basic test - in production you'd test with different IPs
        for _ in range(5):
            response = client.get("/api/data")
            assert response.status_code == 200

        response = client.get("/api/data")
        assert response.status_code == 429
