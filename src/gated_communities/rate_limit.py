"""Rate limiting middleware."""

import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        self._requests: dict[str, list] = {}
        self._limits: dict[str, tuple[int, int]] = {
            "default": (50, 60),
            "auth": (5, 60),
            "health": (50, 2),
        }

    def reset(self):
        """Reset all rate limit state."""
        self._requests.clear()

    def _get_key(self, request: Request) -> str:
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        if path.startswith("/auth"):
            return f"auth:{client_ip}"
        elif path.startswith("/health"):
            return f"health:{client_ip}"
        else:
            return f"default:{client_ip}"

    def _get_limit(self, request: Request) -> tuple[int, int]:
        path = request.url.path
        if path.startswith("/auth"):
            return self._limits["auth"]
        elif path.startswith("/health"):
            return self._limits["health"]
        return self._limits["default"]

    def is_allowed(self, request: Request) -> tuple[bool, dict[str, str]]:
        key = self._get_key(request)
        limit, window = self._get_limit(request)
        now = time.time()

        if key not in self._requests:
            self._requests[key] = []

        self._requests[key] = [t for t in self._requests[key] if now - t < window]

        if len(self._requests[key]) >= limit:
            reset_time = (
                int(self._requests[key][0] + window) if self._requests[key] else int(now + window)
            )
            headers = {
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(max(1, int(reset_time - now))),
            }
            return False, headers

        self._requests[key].append(now)
        remaining = limit - len(self._requests[key])
        reset_time = (
            int(self._requests[key][0] + window) if self._requests[key] else int(now + window)
        )
        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }
        return True, headers


rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting."""

    async def dispatch(self, request: Request, call_next):
        allowed, headers = rate_limiter.is_allowed(request)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers=headers,
            )
        response = await call_next(request)
        for key, value in headers.items():
            response.headers[key] = value
        return response
