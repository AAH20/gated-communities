"""Tests for authentication middleware."""
import pytest
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Create a test FastAPI app with auth middleware."""
    app = FastAPI()

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        # Skip auth for public paths
        public_paths = ["/health", "/docs", "/openapi.json", "/login"]
        if any(request.url.path.startswith(p) for p in public_paths):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"},
            )

        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authentication scheme"},
            )

        # Validate token format (simple check)
        if len(token) < 10:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token"},
            )

        response = await call_next(request)
        return response

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/protected")
    async def protected():
        return {"message": "secret data"}

    @app.get("/login")
    async def login():
        return {"token": "test-token-12345"}

    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestAuthMiddleware:
    """Test suite for authentication middleware."""

    def test_public_path_no_auth_required(self, client):
        """Public paths should be accessible without authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_protected_path_no_auth_header(self, client):
        """Protected paths should return 401 without auth header."""
        response = client.get("/protected")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_protected_path_valid_token(self, client):
        """Protected paths should be accessible with valid token."""
        headers = {"Authorization": "Bearer valid-token-12345"}
        response = client.get("/protected", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "secret data"}

    def test_protected_path_invalid_scheme(self, client):
        """Non-Bearer scheme should return 401."""
        headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        response = client.get("/protected", headers=headers)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid authentication scheme"

    def test_protected_path_short_token(self, client):
        """Short/invalid token should return 401."""
        headers = {"Authorization": "Bearer short"}
        response = client.get("/protected", headers=headers)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"

    def test_protected_path_empty_token(self, client):
        """Empty token should return 401."""
        headers = {"Authorization": "Bearer "}
        response = client.get("/protected", headers=headers)
        assert response.status_code == 401

    def test_protected_path_malformed_header(self, client):
        """Malformed auth header should return 401."""
        headers = {"Authorization": "not-a-valid-header"}
        response = client.get("/protected", headers=headers)
        assert response.status_code == 401

    def test_docs_path_public(self, client):
        """Docs paths should be public."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_path_public(self, client):
        """OpenAPI spec should be public."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_login_path_public(self, client):
        """Login path should be public."""
        response = client.get("/login")
        assert response.status_code == 200
        assert "token" in response.json()

    def test_multiple_protected_requests(self, client):
        """Multiple requests with valid token should all succeed."""
        headers = {"Authorization": "Bearer valid-token-12345"}
        for _ in range(3):
            response = client.get("/protected", headers=headers)
            assert response.status_code == 200

    def test_post_request_requires_auth(self, client):
        """POST requests to protected paths should also require auth."""
        response = client.post("/protected", json={"data": "test"})
        assert response.status_code == 401

    def test_post_request_with_auth(self, client):
        """POST requests with valid auth should succeed."""
        headers = {"Authorization": "Bearer valid-token-12345"}
        response = client.post("/protected", headers=headers, json={"data": "test"})
        assert response.status_code == 200
