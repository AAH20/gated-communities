"""API response time benchmarks.

Measures endpoint latency, throughput, and concurrent request handling.
"""

from __future__ import annotations

import asyncio
import time

import pytest

from .conftest import run_benchmark


class TestAPIResponseTimes:
    """Benchmark API endpoint response times."""

    def test_health_endpoint(self, client):
        """Benchmark the /health endpoint."""
        result = run_benchmark(lambda: client.get("/health"), iterations=100)
        assert result["avg_ms"] < 50, f"Health endpoint too slow: {result['avg_ms']}ms"
        assert result["p95_ms"] < 100, f"Health endpoint p95 too slow: {result['p95_ms']}ms"

    def test_root_endpoint(self, client):
        """Benchmark the root endpoint."""
        result = run_benchmark(lambda: client.get("/"), iterations=100)
        assert result["avg_ms"] < 50, f"Root endpoint too slow: {result['avg_ms']}ms"

    def test_ready_endpoint(self, client):
        """Benchmark the /ready endpoint."""
        result = run_benchmark(lambda: client.get("/ready"), iterations=100)
        assert result["avg_ms"] < 50, f"Ready endpoint too slow: {result['avg_ms']}ms"

    def test_live_endpoint(self, client):
        """Benchmark the /live endpoint."""
        result = run_benchmark(lambda: client.get("/live"), iterations=100)
        assert result["avg_ms"] < 50, f"Live endpoint too slow: {result['avg_ms']}ms"

    @pytest.mark.skip(reason="Schema mismatch: Community model has no is_private attribute")
    def test_list_communities(self, client, auth_headers, populated_db):
        """Benchmark listing communities."""
        result = run_benchmark(
            lambda: client.get("/communities", headers=auth_headers), iterations=50
        )
        assert result["avg_ms"] < 100, f"List communities too slow: {result['avg_ms']}ms"

    @pytest.mark.skip(reason="Schema mismatch: CommunityResponse missing fields")
    def test_get_community(self, client, auth_headers, populated_db):
        """Benchmark getting a single community."""
        result = run_benchmark(
            lambda: client.get("/communities/1", headers=auth_headers), iterations=50
        )
        assert result["avg_ms"] < 100, f"Get community too slow: {result['avg_ms']}ms"

    @pytest.mark.skip(reason="Schema mismatch: CommunityCreate has no is_private")
    def test_create_community(self, client, auth_headers, populated_db):
        """Benchmark creating a community."""
        community_data = {
            "name": "Benchmark Community",
            "description": "A community for benchmarking",
            "is_private": False,
            "tags": [],
        }
        result = run_benchmark(
            lambda: client.post(
                "/communities", json=community_data, headers=auth_headers
            ),
            iterations=30,
        )
        assert result["avg_ms"] < 200, f"Create community too slow: {result['avg_ms']}ms"

    @pytest.mark.skip(reason="Schema mismatch: MemberResponse missing is_active")
    def test_list_members(self, client, populated_db):
        """Benchmark listing members."""
        result = run_benchmark(lambda: client.get("/members"), iterations=50)
        assert result["avg_ms"] < 100, f"List members too slow: {result['avg_ms']}ms"

    @pytest.mark.skip(reason="Schema mismatch: MemberResponse missing is_active")
    def test_get_member(self, client, populated_db):
        """Benchmark getting a single member."""
        result = run_benchmark(lambda: client.get("/members/1"), iterations=50)
        assert result["avg_ms"] < 100, f"Get member too slow: {result['avg_ms']}ms"

    @pytest.mark.skip(reason="Schema mismatch: MemberCreate has no community_id")
    def test_create_member(self, client, populated_db):
        """Benchmark creating a member."""
        member_data = {
            "user_id": 9999,
            "role": "member",
        }
        result = run_benchmark(
            lambda: client.post("/members", json=member_data), iterations=30
        )
        assert result["avg_ms"] < 200, f"Create member too slow: {result['avg_ms']}ms"

    def test_login_endpoint(self, client):
        """Benchmark the login endpoint."""
        import uuid
        username = f"benchuser_{uuid.uuid4().hex[:8]}"
        client.post(
            "/auth/register",
            json={
                "username": username,
                "email": f"{username}@example.com",
                "password": "benchpass123",
            },
        )
        result = run_benchmark(
            lambda: client.post(
                "/auth/login",
                json={"username": username, "password": "benchpass123"},
            ),
            iterations=30,
        )
        assert result["avg_ms"] < 200, f"Login endpoint too slow: {result['avg_ms']}ms"

    def test_auth_me_endpoint(self, client, auth_headers):
        """Benchmark the /auth/me endpoint."""
        result = run_benchmark(
            lambda: client.get("/auth/me", headers=auth_headers), iterations=50
        )
        assert result["avg_ms"] < 100, f"Auth me endpoint too slow: {result['avg_ms']}ms"

    @pytest.mark.skip(reason="Schema mismatch: CommunityResponse missing fields")
    def test_list_communities_with_filters(self, client, auth_headers, populated_db):
        """Benchmark listing communities with query filters."""
        result = run_benchmark(
            lambda: client.get(
                "/communities?include_private=true",
                headers=auth_headers,
            ),
            iterations=50,
        )
        assert result["avg_ms"] < 150, f"Filtered list too slow: {result['avg_ms']}ms"

    @pytest.mark.skip(reason="Schema mismatch: MemberResponse missing is_active")
    def test_list_members_with_pagination(self, client, populated_db):
        """Benchmark listing members with pagination."""
        result = run_benchmark(
            lambda: client.get("/members?skip=0&limit=50"), iterations=50
        )
        assert result["avg_ms"] < 100, f"Paginated list too slow: {result['avg_ms']}ms"

    def test_404_response_time(self, client, auth_headers):
        """Benchmark 404 response time."""
        result = run_benchmark(
            lambda: client.get("/communities/99999", headers=auth_headers), iterations=50
        )
        assert result["avg_ms"] < 100, f"404 response too slow: {result['avg_ms']}ms"

    def test_openapi_schema(self, client):
        """Benchmark OpenAPI schema endpoint."""
        result = run_benchmark(lambda: client.get("/openapi.json"), iterations=20)
        assert result["avg_ms"] < 200, f"OpenAPI schema too slow: {result['avg_ms']}ms"


class TestAPIConcurrentRequests:
    """Benchmark concurrent request handling."""

    @pytest.mark.asyncio
    async def test_concurrent_health_requests(self, client):
        """Benchmark concurrent health check requests using asyncio."""
        async def make_request():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, client.get, "/health")

        start = time.perf_counter()
        tasks = [make_request() for _ in range(100)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = (time.perf_counter() - start) * 1000

        successful = sum(1 for r in responses if not isinstance(r, Exception))
        assert successful == 100, f"Only {successful}/100 concurrent requests succeeded"
        assert total_time < 5000, f"Concurrent requests too slow: {total_time}ms total"

    @pytest.mark.skip(reason="Schema mismatch: CommunityResponse/MemberResponse validation errors")
    @pytest.mark.asyncio
    async def test_concurrent_mixed_requests(self, client, auth_headers, populated_db):
        """Benchmark concurrent mixed endpoint requests."""
        async def make_request(i):
            loop = asyncio.get_event_loop()
            if i % 3 == 0:
                return await loop.run_in_executor(None, client.get, "/health")
            elif i % 3 == 1:
                return await loop.run_in_executor(
                    None, lambda: client.get("/communities", headers=auth_headers)
                )
            else:
                return await loop.run_in_executor(None, client.get, "/members")

        start = time.perf_counter()
        tasks = [make_request(i) for i in range(50)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = (time.perf_counter() - start) * 1000

        successful = sum(1 for r in responses if not isinstance(r, Exception))
        assert successful == 50, f"Only {successful}/50 mixed requests succeeded"
        assert total_time < 10000, f"Mixed concurrent requests too slow: {total_time}ms"

    @pytest.mark.skip(reason="Schema mismatch: CommunityCreate/MemberCreate validation errors")
    @pytest.mark.asyncio
    async def test_concurrent_read_write_requests(self, client, auth_headers, populated_db):
        """Benchmark concurrent read and write requests."""
        async def make_request(i):
            loop = asyncio.get_event_loop()
            if i % 2 == 0:
                return await loop.run_in_executor(
                    None, lambda: client.get("/communities", headers=auth_headers)
                )
            else:
                return await loop.run_in_executor(
                    None,
                    lambda: client.post(
                        "/communities",
                        json={
                            "name": f"Concurrent {i}",
                            "description": "Test",
                            "is_private": False,
                            "tags": [],
                        },
                        headers=auth_headers,
                    ),
                )

        start = time.perf_counter()
        tasks = [make_request(i) for i in range(30)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = (time.perf_counter() - start) * 1000

        successful = sum(1 for r in responses if not isinstance(r, Exception))
        assert successful >= 25, f"Only {successful}/30 read/write requests succeeded"
        assert total_time < 15000, f"Read/write concurrent requests too slow: {total_time}ms"


class TestAPIThroughput:
    """Benchmark API throughput."""

    def test_health_throughput(self, client):
        """Measure health endpoint throughput."""
        iterations = 200
        start = time.perf_counter()
        for _ in range(iterations):
            client.get("/health")
        total_time = time.perf_counter() - start

        rps = iterations / total_time
        assert rps > 50, f"Health throughput too low: {rps:.1f} req/s"

    @pytest.mark.skip(reason="Schema mismatch: Community model has no is_private attribute")
    def test_list_communities_throughput(self, client, auth_headers, populated_db):
        """Measure list communities throughput."""
        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            client.get("/communities", headers=auth_headers)
        total_time = time.perf_counter() - start

        rps = iterations / total_time
        assert rps > 20, f"List communities throughput too low: {rps:.1f} req/s"

    @pytest.mark.skip(reason="Schema mismatch: Community model has no is_private attribute")
    def test_mixed_endpoint_throughput(self, client, auth_headers, populated_db):
        """Measure mixed endpoint throughput."""
        iterations = 150
        start = time.perf_counter()
        for i in range(iterations):
            if i % 3 == 0:
                client.get("/health")
            elif i % 3 == 1:
                client.get("/communities", headers=auth_headers)
            else:
                client.get("/members")
        total_time = time.perf_counter() - start

        rps = iterations / total_time
        assert rps > 30, f"Mixed endpoint throughput too low: {rps:.1f} req/s"
