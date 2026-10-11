"""Local configuration for the performance suite.

Load/stress/endurance tests deliberately generate far more than the default
rate-limit (50 requests / window).  The rate limiter itself is exercised by the
security and middleware suites, so here we neutralise it: a load test measures
application capacity, not the throttle.  Without this the harness would record
thousands of ``HTTP 429`` responses and the assertions would be meaningless.
"""
from __future__ import annotations

from typing import Any

import pytest

from gated_communities.rate_limit import rate_limiter


@pytest.fixture(autouse=True)
def disable_rate_limit(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Make every request allowed for the duration of each perf test."""
    monkeypatch.setattr(
        rate_limiter, "is_allowed", lambda request: (True, {})  # noqa: ARG005
    )
    rate_limiter.reset()
    yield
    rate_limiter.reset()
