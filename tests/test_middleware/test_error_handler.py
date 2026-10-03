"""Tests for error handling middleware."""
import pytest
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException


@pytest.fixture
def app():
    """Create a test FastAPI app with error handling middleware."""
    app = FastAPI()

    @app.middleware("http")
    async def error_handler_middleware(request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "code": exc.status_code,
                        "message": exc.detail,
                        "type": "http_error",
                    }
                },
            )
        except StarletteHTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "code": exc.status_code,
                        "message": exc.detail,
                        "type": "starlette_error",
                    }
                },
            )
        except ValueError as exc:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": 400,
                        "message": str(exc),
                        "type": "validation_error",
                    }
                },
            )
        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": 500,
                        "message": "Internal server error",
                        "type": "internal_error",
                    }
                },
            )

    @app.get("/ok")
    async def ok():
        return {"status": "ok"}

    @app.get("/http-error")
    async def http_error():
        raise HTTPException(status_code=404, detail="Resource not found")

    @app.get("/value-error")
    async def value_error():
        raise ValueError("Invalid input value")

    @app.get("/runtime-error")
    async def runtime_error():
        raise RuntimeError("Something went wrong")

    @app.get("/zero-division")
    async def zero_division():
        1 / 0

    @app.get("/custom-status")
    async def custom_status():
        raise HTTPException(status_code=403, detail="Access forbidden")

    return app


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


class TestErrorHandlerMiddleware:
    """Test suite for error handling middleware."""

    def test_successful_request(self, client):
        """Successful requests should pass through normally."""
        response = client.get("/ok")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_http_exception_handled(self, client):
        """HTTPException should be caught and formatted."""
        response = client.get("/http-error")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == 404
        assert data["error"]["message"] == "Resource not found"
        assert data["error"]["type"] == "http_error"

    def test_value_error_handled(self, client):
        """ValueError should return 400 with validation_error type."""
        response = client.get("/value-error")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == 400
        assert data["error"]["message"] == "Invalid input value"
        assert data["error"]["type"] == "validation_error"

    def test_runtime_error_handled(self, client):
        """RuntimeError should return 500 with internal_error type."""
        response = client.get("/runtime-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == 500
        assert data["error"]["message"] == "Internal server error"
        assert data["error"]["type"] == "internal_error"

    def test_zero_division_error_handled(self, client):
        """ZeroDivisionError should return 500."""
        response = client.get("/zero-division")
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == 500
        assert data["error"]["type"] == "internal_error"

    def test_custom_http_status(self, client):
        """Custom HTTP status codes should be preserved."""
        response = client.get("/custom-status")
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == 403
        assert data["error"]["message"] == "Access forbidden"

    def test_error_response_structure(self, client):
        """Error responses should have consistent structure."""
        response = client.get("/http-error")
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "type" in data["error"]

    def test_error_response_content_type(self, client):
        """Error responses should be JSON."""
        response = client.get("/http-error")
        assert response.headers["content-type"].startswith("application/json")

    def test_multiple_error_types(self, client):
        """Different error types should be handled appropriately."""
        # HTTP error
        response = client.get("/http-error")
        assert response.status_code == 404
        assert response.json()["error"]["type"] == "http_error"

        # Value error
        response = client.get("/value-error")
        assert response.status_code == 400
        assert response.json()["error"]["type"] == "validation_error"

        # Runtime error
        response = client.get("/runtime-error")
        assert response.status_code == 500
        assert response.json()["error"]["type"] == "internal_error"

    def test_no_error_leaks_stack_trace(self, client):
        """Internal errors should not leak stack traces."""
        response = client.get("/runtime-error")
        data = response.json()
        assert "traceback" not in str(data).lower()
        assert "stack" not in str(data).lower()
        # Should return generic message
        assert data["error"]["message"] == "Internal server error"

    def test_404_for_unknown_route(self, client):
        """Unknown routes should return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
