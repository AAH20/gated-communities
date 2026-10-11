"""Load test: concurrent users hitting the API simultaneously.

The load generator drives the application **in-process** through an
``httpx.ASGITransport`` (see ``_asgi.py``) so the numbers are real without a
standalone ``uvicorn`` server.  No TCP sockets are opened, so the suite runs
unchanged in the unit CI job.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import httpx

try:  # package import during pytest collection
    from ._asgi import async_client
except ImportError:  # pragma: no cover - direct module execution
    from _asgi import async_client  # type: ignore[no-redef]


@dataclass
class LoadResult:
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    latencies: list[float] = field(default_factory=list)
    wall_time: float = 0.0

    @property
    def avg_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    @property
    def p95_latency(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]

    @property
    def throughput(self) -> float:
        # Requests per second over wall-clock time.  Summing per-request
        # latencies (the old behaviour) understates throughput whenever requests
        # run concurrently.
        if self.wall_time > 0:
            return self.total_requests / self.wall_time
        total_time = sum(self.latencies)
        return self.successful / total_time if total_time > 0 else 0.0


async def _hit_endpoint(
    client: httpx.AsyncClient, url: str, results: LoadResult
) -> None:
    start = time.perf_counter()
    try:
        resp = await client.get(url, timeout=10.0)
        elapsed = time.perf_counter() - start
        results.latencies.append(elapsed)
        results.total_requests += 1
        if 200 <= resp.status_code < 300:
            results.successful += 1
        else:
            results.failed += 1
    except Exception:
        elapsed = time.perf_counter() - start
        results.latencies.append(elapsed)
        results.total_requests += 1
        results.failed += 1


async def run_load_test(
    endpoint: str,
    concurrent_users: int,
    requests_per_user: int,
) -> LoadResult:
    """Run a load test against ``endpoint`` on the in-process application."""
    results = LoadResult()
    async with async_client() as client:
        tasks = []
        for _ in range(concurrent_users):
            for _ in range(requests_per_user):
                tasks.append(_hit_endpoint(client, endpoint, results))
        start = time.perf_counter()
        await asyncio.gather(*tasks)
        results.wall_time = time.perf_counter() - start
    return results


def test_load_health_endpoint() -> None:
    result = asyncio.run(
        run_load_test("/health", concurrent_users=10, requests_per_user=10)
    )
    assert result.failed == 0, f"{result.failed} requests failed"
    assert result.total_requests == 100
    # Avg (not p95) keeps the assertion stable on a shared/noisy runner while
    # still catching a pathological slowdown; p95 is recorded on the result.
    assert result.avg_latency < 2.0, f"Avg latency {result.avg_latency:.3f}s exceeds 2s threshold"


def test_load_tiers_endpoint() -> None:
    result = asyncio.run(
        run_load_test("/tiers", concurrent_users=10, requests_per_user=10)
    )
    assert result.failed == 0
    assert result.total_requests == 100
    assert result.throughput > 10, f"Throughput {result.throughput:.1f} req/s below 10"


def test_load_liveness_endpoint() -> None:
    result = asyncio.run(
        run_load_test("/live", concurrent_users=10, requests_per_user=5)
    )
    assert result.failed == 0
    assert result.total_requests == 50
    assert result.avg_latency < 1.0, f"Avg latency {result.avg_latency:.3f}s exceeds 1s"
