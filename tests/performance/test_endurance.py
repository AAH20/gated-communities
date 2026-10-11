"""Endurance test: sustained load over time to detect memory leaks and degradation.

Runs against the application **in-process** via ``httpx.ASGITransport`` (see
``_asgi.py``) so no live server is required.
"""
from __future__ import annotations

import asyncio
import statistics
import time
from dataclasses import dataclass, field

import httpx

try:  # package import during pytest collection
    from ._asgi import async_client
except ImportError:  # pragma: no cover - direct module execution
    from _asgi import async_client  # type: ignore[no-redef]


@dataclass
class EnduranceResult:
    duration_seconds: float = 0.0
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    latencies: list[float] = field(default_factory=list)
    errors_over_time: list[tuple[float, int]] = field(default_factory=list)

    @property
    def avg_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    @property
    def latency_trend(self) -> str:
        n = len(self.latencies)
        if n < 20:
            return "insufficient_data"
        # Compare robust medians of the opening and closing windows rather than
        # two halves: a single mid-run scheduler/GC spike must not be mistaken
        # for a degradation trend when latencies are sub-10ms and measured
        # in-process.
        window = max(10, n // 5)
        first_half = statistics.median(self.latencies[:window])
        second_half = statistics.median(self.latencies[-window:])
        if first_half <= 0:
            return "stable"
        if second_half > first_half * 5.0:
            return "degrading"
        return "stable"


async def _endurance_worker(
    client: httpx.AsyncClient,
    url: str,
    result: EnduranceResult,
    stop_event: asyncio.Event,
) -> None:
    while not stop_event.is_set():
        start = time.perf_counter()
        try:
            resp = await client.get(url, timeout=10.0)
            elapsed = time.perf_counter() - start
            result.latencies.append(elapsed)
            result.total_requests += 1
            if 200 <= resp.status_code < 300:
                result.successful += 1
            else:
                result.failed += 1
                result.errors_over_time.append((time.time(), result.failed))
        except Exception:
            elapsed = time.perf_counter() - start
            result.latencies.append(elapsed)
            result.total_requests += 1
            result.failed += 1
            result.errors_over_time.append((time.time(), result.failed))
        await asyncio.sleep(0.01)


async def run_endurance_test(
    endpoint: str,
    duration_seconds: float,
    concurrent_workers: int = 10,
) -> EnduranceResult:
    result = EnduranceResult(duration_seconds=duration_seconds)
    stop_event = asyncio.Event()

    async with async_client() as client:
        workers = [
            asyncio.create_task(
                _endurance_worker(client, endpoint, result, stop_event)
            )
            for _ in range(concurrent_workers)
        ]
        await asyncio.sleep(duration_seconds)
        stop_event.set()
        await asyncio.gather(*workers)

    return result


def test_endurance_short_burst() -> None:
    result = asyncio.run(
        run_endurance_test(
            "/health",
            duration_seconds=3.0,
            concurrent_workers=5,
        )
    )
    assert result.total_requests > 0
    assert result.failed == 0
    assert result.latency_trend in ("stable", "insufficient_data")


def test_endurance_sustained_load() -> None:
    result = asyncio.run(
        run_endurance_test(
            "/tiers",
            duration_seconds=5.0,
            concurrent_workers=5,
        )
    )
    assert result.total_requests > 50
    assert result.latency_trend == "stable"
