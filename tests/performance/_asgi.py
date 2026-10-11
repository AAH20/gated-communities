"""Shared in-process ASGI transport for the performance suite.

Performance/load/stress/endurance/scalability tests must exercise the real
application **without** a live network dependency.  Historically these tests
hard-coded ``http://localhost:8000`` and failed in CI with
``All connection attempts failed`` (``error_rate == 1.0``) because no
``uvicorn`` server is running during the unit-test job.

Instead we drive ``gated_communities.main:app`` directly through
``httpx.ASGITransport``: the request never leaves the process, so no TCP
socket is opened and the measured numbers are real.
"""
from __future__ import annotations

import httpx

from gated_communities.main import app

#: Pseudo base URL used for in-process requests.  It is a routing placeholder
#: only and is never resolved over the network (``ASGITransport`` short-circuits
#: it straight into the ASGI app).
TEST_BASE_URL = "http://testserver"


def asgi_transport() -> httpx.ASGITransport:
    """Return an ASGI transport bound to the application under test."""
    return httpx.ASGITransport(app=app)


def async_client(**kwargs: object) -> httpx.AsyncClient:
    """Return an ``httpx.AsyncClient`` wired to the in-process app.

    No real network — safe to use in CI without a running server.
    """
    kwargs.setdefault("base_url", TEST_BASE_URL)
    return httpx.AsyncClient(transport=asgi_transport(), **kwargs)  # type: ignore[arg-type]
