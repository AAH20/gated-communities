"""Guard tests: the performance harness must not open real network sockets.

Regression guard for the CI failure where the load/stress/scalability harnesses
dialed ``http://localhost:8000`` and produced ``All connection attempts failed``
(``error_rate == 1.0``).  Here we block ``socket.socket.connect`` entirely and
assert the in-process harness still completes — proving every request is served
through the ASGI transport and never leaves the process.
"""
from __future__ import annotations

import asyncio
import socket

import pytest

try:  # package import during pytest collection
    from . import test_load, test_scalability, test_stress
except ImportError:  # pragma: no cover - direct module execution
    import test_load  # type: ignore[no-redef]
    import test_scalability  # type: ignore[no-redef]
    import test_stress  # type: ignore[no-redef]


def _forbid_connect(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("performance harness attempted a real network connection")

    monkeypatch.setattr(socket.socket, "connect", _blocked)


def test_load_harness_needs_no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    _forbid_connect(monkeypatch)
    result = asyncio.run(
        test_load.run_load_test("/health", concurrent_users=5, requests_per_user=4)
    )
    assert result.total_requests == 20
    assert result.failed == 0


def test_stress_harness_needs_no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    _forbid_connect(monkeypatch)
    result = asyncio.run(test_stress._run_at_concurrency("/health", 5, 10))
    assert result.total_requests == 10
    assert result.error_rate == 0.0


def test_scalability_harness_needs_no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    _forbid_connect(monkeypatch)
    result = asyncio.run(
        test_scalability.run_scalability_test(["in-process"], requests_per_instance=10)
    )
    assert result.successful == 10
