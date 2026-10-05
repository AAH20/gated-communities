"""Regression tests: routers must actually mount, and skips must not be silent.

register_all_routers() skips routers whose imports fail or that declare an
empty-prefix root path. Each skip is logged and recorded, but a skipped router
means its endpoints 404 with no test failing — CI stays green on a broken API
surface. These tests assert the routers are mounted and that nothing was
silently dropped.

Note on route enumeration: this FastAPI version wraps included routers rather
than flattening them into `Route` objects on `app.routes`, so counting with
`hasattr(r, "path")` under-reports (it sees 11 of 80). These tests therefore
assert against live HTTP responses, which is what actually matters.
"""

from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_PATH", os.path.join(tempfile.mkdtemp(), "tiers.db"))

from gated_communities.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.parametrize(
    "prefix",
    [
        "/compliance/audits",
        "/compliance/policies",
        "/compliance/scores",
        "/compliance/violations",
    ],
)
def test_compliance_router_is_reachable(client: TestClient, prefix: str) -> None:
    """The four compliance routers must serve requests, not 404 as unmounted."""
    response = client.get(prefix)
    assert response.status_code != 404, (
        f"{prefix} returned 404; the router was not mounted"
    )
    # 200 when unauthenticated read is allowed; 401/403 when auth is enforced.
    assert response.status_code in (200, 401, 403), (
        f"{prefix} returned {response.status_code}"
    )


@pytest.mark.parametrize("path", ["/health", "/health/ready"])
def test_health_endpoints_respond(client: TestClient, path: str) -> None:
    """Health endpoints must be mounted and report healthy."""
    response = client.get(path)
    assert response.status_code == 200, f"{path} returned {response.status_code}"


def test_no_router_is_silently_skipped() -> None:
    """register_all_routers must record its skips; there must be none left."""
    skipped = getattr(app.state, "skipped_routers", None)
    assert skipped is not None, "app.state.skipped_routers missing; skips are silent"
    assert skipped == {}, f"routers still skipped: {skipped}"