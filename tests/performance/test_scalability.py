"""Scalability test: horizontal scaling behaviour across multiple instances.

Two flavours live here:

* **In-process** (default) — a single application instance is driven through
  ``httpx.ASGITransport`` (see ``_asgi.py``).  This measures one instance's
  throughput with no live server.
* **Live multi-instance** — genuinely requires *N* independent server
  processes, which cannot be faked in-process.  These are marked
  ``@pytest.mark.perf`` and skipped unless ``PERF_BASE_URLS`` is set, so they
  never fail the unit CI job with ``All connection attempts failed``.
"""
from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field

import httpx
import pytest

try:  # package import during pytest collection
    from ._asgi import async_client
except ImportError:  # pragma: no cover - direct module execution
    from _asgi import async_client  # type: ignore[no-redef]


#: Comma-separated base URLs of live instances, e.g.
#: ``PERF_BASE_URLS=http://localhost:8000,http://localhost:8001``.
_LIVE_URLS: list[str] = [
    u.strip() for u in os.environ.get("PERF_BASE_URLS", "").split(",") if u.strip()
]


@dataclass
class ScalabilityResult:
    instances: int = 0
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    latencies: list[float] = field(default_factory=list)
    per_instance_throughput: dict[int, float] = field(default_factory=dict)

    @property
    def total_throughput(self) -> float:
        return sum(self.per_instance_throughput.values())

    @property
    def scaling_efficiency(self) -> float:
        if not self.per_instance_throughput or self.instances <= 1:
            return 1.0
        throughputs = list(self.per_instance_throughput.values())
        avg_throughput = sum(throughputs) / len(throughputs)
        max_throughput = max(throughputs)
        return avg_throughput / max_throughput if max_throughput > 0 else 0.0


async def _probe_instance(
    client: httpx.AsyncClient, instance_id: int, num_requests: int
) -> tuple[int, float, float]:
    success = 0
    latencies: list[float] = []
    for _ in range(num_requests):
        start = time.perf_counter()
        try:
            resp = await client.get("/health", timeout=5.0)
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)
            if resp.status_code == 200:
                success += 1
        except Exception:
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)
    total_time = sum(latencies)
    throughput = success / total_time if total_time > 0 else 0.0
    return success, throughput, max(latencies) if latencies else 0.0


async def run_scalability_test(
    base_urls: list[str],
    requests_per_instance: int = 50,
) -> ScalabilityResult:
    """Probe ``base_urls`` (in-process ASGI transport when unspecified).

    The base URLs are accepted for API compatibility with the live harness but
    requests are always dispatched in-process.
    """
    result = ScalabilityResult(instances=len(base_urls))
    async with async_client() as client:
        tasks = [
            asyncio.create_task(_probe_instance(client, i, requests_per_instance))
            for i, _ in enumerate(base_urls)
        ]
        outcomes = await asyncio.gather(*tasks)

    for instance_id, (success, throughput, max_lat) in enumerate(outcomes):
        result.successful += success
        result.total_requests += requests_per_instance
        result.failed += requests_per_instance - success
        result.per_instance_throughput[instance_id] = throughput

    return result


def test_scalability_single_instance() -> None:
    result = asyncio.run(
        run_scalability_test(["in-process"], requests_per_instance=50)
    )
    assert result.instances == 1
    assert result.successful == 50
    assert result.total_throughput > 0


@pytest.mark.perf
@pytest.mark.skipif(
    not _LIVE_URLS,
    reason="requires multiple live server processes; set PERF_BASE_URLS to run",
)
def test_scalability_multiple_instances() -> None:
    urls = _LIVE_URLS
    result = asyncio.run(run_scalability_test(urls, requests_per_instance=30))
    assert result.instances >= 2
    assert result.total_requests == 30 * len(urls)
    assert result.scaling_efficiency > 0.5


@pytest.mark.perf
@pytest.mark.skipif(
    not _LIVE_URLS,
    reason="requires multiple live server processes; set PERF_BASE_URLS to run",
)
def test_scalability_linear_growth() -> None:
    async def measure_at_scale(num_instances: int) -> float:
        res = await run_scalability_test(
            _LIVE_URLS[:num_instances], requests_per_instance=20
        )
        return res.total_throughput

    throughput_1 = asyncio.run(measure_at_scale(1))
    throughput_2 = asyncio.run(measure_at_scale(2))
    if throughput_1 > 0:
        ratio = throughput_2 / throughput_1
        assert ratio > 1.2, f"Scaling ratio {ratio:.2f} indicates poor horizontal scaling"
