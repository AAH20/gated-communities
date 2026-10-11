"""Performance smoke tests using the in-process ``TestClient``.

These do not require ``pytest-benchmark`` (which is not installed in CI) — a
plain ``time.perf_counter`` measurement keeps the assertions self-contained
while still exercising the real application in-process.
"""

from __future__ import annotations

import concurrent.futures
import time

from fastapi.testclient import TestClient


class TestPerformance:
    def test_health_check_performance(self, client: TestClient) -> None:
        start = time.perf_counter()
        result = client.get("/health")
        elapsed = time.perf_counter() - start
        assert result.status_code == 200
        assert elapsed < 1.0, f"/health took {elapsed:.3f}s"

    def test_tiers_list_performance(self, client: TestClient) -> None:
        start = time.perf_counter()
        result = client.get("/tiers")
        elapsed = time.perf_counter() - start
        assert result.status_code == 200
        assert elapsed < 1.0, f"/tiers took {elapsed:.3f}s"

    def test_liveness_performance(self, client: TestClient) -> None:
        start = time.perf_counter()
        result = client.get("/live")
        elapsed = time.perf_counter() - start
        assert result.status_code == 200
        assert elapsed < 1.0, f"/live took {elapsed:.3f}s"

    def test_concurrent_requests(self, client: TestClient) -> None:
        def make_request():
            return client.get("/health")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(r.status_code == 200 for r in results)
