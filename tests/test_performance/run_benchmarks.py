#!/usr/bin/env python3
"""Performance benchmark runner for gated-communities.

Runs all performance benchmarks, collects results, and generates a report
with bottleneck identification.

Usage:
    python -m tests.test_performance.run_benchmarks
    python tests/test_performance/run_benchmarks.py
"""

from __future__ import annotations

import asyncio
import json
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "http://testserver"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


@dataclass
class BenchmarkResult:
    name: str
    category: str
    metrics: dict[str, Any] = field(default_factory=dict)
    raw_data: list[float] = field(default_factory=list)


def _stats(times: list[float]) -> dict[str, float]:
    """Compute min/avg/max for positive timings."""
    valid = [t for t in times if t > 0]
    if not valid:
        return {"avg_ms": 0, "min_ms": 0, "max_ms": 0}
    return {
        "avg_ms": round(statistics.mean(valid), 2),
        "min_ms": round(min(valid), 2),
        "max_ms": round(max(valid), 2),
    }


def _pct(sorted_vals: list[float], p: float) -> float:
    """Return percentile from pre-sorted values."""
    if not sorted_vals:
        return 0
    return round(sorted_vals[min(int(len(sorted_vals) * p), len(sorted_vals) - 1)], 2)


def run_sync_benchmark(
    func: Any, iterations: int = 50, warmup: int = 5
) -> dict[str, Any]:
    """Run a sync benchmark function and return timing statistics."""
    for _ in range(warmup):
        func()
    times: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    sorted_times = sorted(times)
    return {
        "avg_ms": round(statistics.mean(times), 3),
        "min_ms": round(min(times), 3),
        "max_ms": round(max(times), 3),
        "median_ms": round(statistics.median(times), 3),
        "p95_ms": round(sorted_times[int(len(sorted_times) * 0.95)], 3),
        "p99_ms": round(sorted_times[int(len(sorted_times) * 0.99)], 3),
        "stdev_ms": round(statistics.stdev(times), 3) if len(times) > 1 else 0,
        "iterations": iterations,
        "total_ms": round(sum(times), 3),
    }


async def run_async_benchmark(
    func: Any, iterations: int = 50, warmup: int = 5
) -> dict[str, Any]:
    """Run an async benchmark function and return timing statistics."""
    for _ in range(warmup):
        await func()
    times: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        await func()
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    sorted_times = sorted(times)
    return {
        "avg_ms": round(statistics.mean(times), 3),
        "min_ms": round(min(times), 3),
        "max_ms": round(max(times), 3),
        "median_ms": round(statistics.median(times), 3),
        "p95_ms": round(sorted_times[int(len(sorted_times) * 0.95)], 3),
        "p99_ms": round(sorted_times[int(len(sorted_times) * 0.99)], 3),
        "stdev_ms": round(statistics.stdev(times), 3) if len(times) > 1 else 0,
        "iterations": iterations,
        "total_ms": round(sum(times), 3),
    }


# ============================================================================
# API Benchmarks
# ============================================================================


def benchmark_api_endpoints(client: Any) -> list[BenchmarkResult]:
    """Benchmark all API endpoints."""
    results = []
    endpoints = [
        ("health", "/health", "GET"),
        ("root", "/", "GET"),
        ("ready", "/ready", "GET"),
        ("live", "/live", "GET"),
    ]
    for name, path, method in endpoints:
        times: list[float] = []
        for _ in range(100):
            start = time.perf_counter()
            client.get(path)
            times.append((time.perf_counter() - start) * 1000)
        results.append(
            BenchmarkResult(
                name=f"api_{name}",
                category="API",
                metrics=_stats(times),
                raw_data=times,
            )
        )
    return results


def benchmark_api_authenticated(client: Any, auth_headers: dict) -> list[BenchmarkResult]:
    """Benchmark authenticated API endpoints."""
    results = []
    endpoints = [
        ("list_communities", "/communities"),
        ("list_members", "/members"),
    ]
    for name, path in endpoints:
        times: list[float] = []
        for _ in range(50):
            start = time.perf_counter()
            client.get(path, headers=auth_headers)
            times.append((time.perf_counter() - start) * 1000)
        results.append(
            BenchmarkResult(
                name=f"api_{name}",
                category="API",
                metrics=_stats(times),
                raw_data=times,
            )
        )
    return results


def benchmark_api_writes(client: Any, auth_headers: dict) -> list[BenchmarkResult]:
    """Benchmark API write operations."""
    results = []
    # Create community
    times: list[float] = []
    for i in range(30):
        start = time.perf_counter()
        client.post(
            "/communities",
            json={
                "name": f"Bench Community {i}",
                "description": "Benchmark",
                "is_private": False,
                "tags": [],
            },
            headers=auth_headers,
        )
        times.append((time.perf_counter() - start) * 1000)
    results.append(
        BenchmarkResult(
            name="api_create_community",
            category="API",
            metrics=_stats(times),
            raw_data=times,
        )
    )
    return results


# ============================================================================
# Database Benchmarks
# ============================================================================


def benchmark_database_queries(db_session: Any) -> list[BenchmarkResult]:
    """Benchmark database queries."""
    from sqlalchemy import text

    results = []
    queries = [
        ("simple_select", "SELECT 1"),
        ("count_communities", "SELECT COUNT(*) FROM communities"),
        ("count_members", "SELECT COUNT(*) FROM members"),
        ("count_moderation", "SELECT COUNT(*) FROM moderation_items"),
        ("count_audit", "SELECT COUNT(*) FROM audit_logs"),
        (
            "join_communities_members",
            "SELECT c.name, COUNT(m.id) FROM communities c "
            "LEFT JOIN members m ON m.community_id = c.id "
            "GROUP BY c.name LIMIT 100",
        ),
        (
            "filter_by_tier",
            "SELECT * FROM communities WHERE tier = 'FREE' LIMIT 50",
        ),
        (
            "filter_by_status",
            "SELECT * FROM communities WHERE status = 'ACTIVE' LIMIT 50",
        ),
        (
            "order_by_name",
            "SELECT * FROM communities ORDER BY name LIMIT 50",
        ),
        (
            "paginated_members",
            "SELECT * FROM members LIMIT 50 OFFSET 50",
        ),
        (
            "aggregate_member_count",
            "SELECT community_id, COUNT(*) FROM members GROUP BY community_id",
        ),
        (
            "text_search",
            "SELECT * FROM communities WHERE name LIKE '%Community%' LIMIT 20",
        ),
    ]
    for name, query in queries:
        times: list[float] = []
        for _ in range(50):
            start = time.perf_counter()
            db_session.execute(text(query))
            times.append((time.perf_counter() - start) * 1000)
        results.append(
            BenchmarkResult(
                name=f"db_{name}",
                category="Database",
                metrics=_stats(times),
                raw_data=times,
            )
        )
    return results


def benchmark_database_orm(db_session: Any) -> list[BenchmarkResult]:
    """Benchmark ORM queries."""
    from gated_communities.models import Community, CommunityStatus, CommunityTier, Member

    results = []
    # ORM queries
    queries = [
        ("orm_all_communities", lambda: db_session.query(Community).all()),
        ("orm_all_members", lambda: db_session.query(Member).all()),
        (
            "orm_filter_tier",
            lambda: db_session.query(Community)
            .filter(Community.tier == CommunityTier.FREE)
            .all(),
        ),
        (
            "orm_filter_status",
            lambda: db_session.query(Community)
            .filter(Community.status == CommunityStatus.ACTIVE)
            .all(),
        ),
        (
            "orm_filter_members_community",
            lambda: db_session.query(Member)
            .filter(Member.community_id == 1)
            .all(),
        ),
        (
            "orm_order_communities",
            lambda: db_session.query(Community)
            .order_by(Community.name)
            .all(),
        ),
        (
            "orm_paginated_members",
            lambda: db_session.query(Member).offset(50).limit(50).all(),
        ),
    ]
    for name, query_fn in queries:
        times: list[float] = []
        for _ in range(50):
            start = time.perf_counter()
            query_fn()
            times.append((time.perf_counter() - start) * 1000)
        results.append(
            BenchmarkResult(
                name=f"db_{name}",
                category="Database",
                metrics=_stats(times),
                raw_data=times,
            )
        )
    return results


# ============================================================================
# Agent Benchmarks
# ============================================================================


async def benchmark_agents() -> list[BenchmarkResult]:
    """Benchmark agent execution times."""
    results = []

    # Trust Scorer
    try:
        from gated_communities.agents.member_verification.trust_scorer import (
            TrustScorerAgent,
        )
        trust_agent = TrustScorerAgent()
        times = []
        for _ in range(50):
            start = time.perf_counter()
            await trust_agent.run(
                {"member_id": "user_123", "include_history": True, "factors": None}
            )
            times.append((time.perf_counter() - start) * 1000)
        results.append(
            BenchmarkResult(
                name="agent_trust_scorer",
                category="Agent",
                metrics=_stats(times),
                raw_data=times,
            )
        )
    except (ImportError, ModuleNotFoundError) as e:
        print(f"  Skipping trust_scorer: {e}")

    # Community Health Scorer
    try:
        from gated_communities.agents.community_health_scorer import (
            calculate_health_score,
            identify_risks,
            get_health_metrics,
            score_community_health,
        )
        for name, func, arg in [
            ("health_score", calculate_health_score, "comm_alpha"),
            ("identify_risks", identify_risks, "comm_beta"),
            ("health_metrics", get_health_metrics, "comm_gamma"),
            ("score_community", score_community_health, "comm_delta"),
        ]:
            times = []
            for _ in range(100):
                start = time.perf_counter()
                func(arg)
                times.append((time.perf_counter() - start) * 1000)
            results.append(
                BenchmarkResult(
                    name=f"agent_{name}",
                    category="Agent",
                    metrics=_stats(times),
                    raw_data=times,
                )
            )
    except (ImportError, ModuleNotFoundError) as e:
        print(f"  Skipping community_health_scorer: {e}")

    # Reputation System
    try:
        from gated_communities.agents.reputation_system import (
            calculate_reputation,
            get_reputation_score,
            update_reputation,
        )
        for name, func, arg in [
            ("calc_reputation", calculate_reputation, "user_123"),
            ("get_reputation", get_reputation_score, "user_123"),
            ("update_reputation", lambda: update_reputation("user_bench", "upvote"), None),
        ]:
            times = []
            for _ in range(100):
                start = time.perf_counter()
                if arg is not None:
                    func(arg)
                else:
                    func()
                times.append((time.perf_counter() - start) * 1000)
            results.append(
                BenchmarkResult(
                    name=f"agent_{name}",
                    category="Agent",
                    metrics=_stats(times),
                    raw_data=times,
                )
            )
    except (ImportError, ModuleNotFoundError) as e:
        print(f"  Skipping reputation_system: {e}")

    # Escalation Workflow
    try:
        from gated_communities.agents.escalation_workflow import (
            create_escalation,
            get_escalation_status,
            resolve_escalation,
        )
        esc = create_escalation("issue_bench", "high")
        esc_id = esc["escalation_id"]
        for name, func, arg in [
            ("create_escalation", lambda: create_escalation("issue_new", "medium"), None),
            ("get_escalation", get_escalation_status, esc_id),
            ("resolve_escalation", resolve_escalation, esc_id),
        ]:
            times = []
            for _ in range(50):
                start = time.perf_counter()
                if arg is not None:
                    func(arg)
                else:
                    func()
                times.append((time.perf_counter() - start) * 1000)
            results.append(
                BenchmarkResult(
                    name=f"agent_{name}",
                    category="Agent",
                    metrics=_stats(times),
                    raw_data=times,
                )
            )
    except (ImportError, ModuleNotFoundError) as e:
        print(f"  Skipping escalation_workflow: {e}")

    # Auto Moderator
    try:
        from gated_communities.agents.moderation_queue.auto_moderator import (
            AutoModeratorAgent,
        )
        mod_agent = AutoModeratorAgent()
        contexts = [
            ("mod_approve", {"content": "Normal content", "content_type": "text", "metadata": {}}),
            ("mod_reject", {"content": "hate speech", "content_type": "text", "metadata": {}}),
            ("mod_escalate", {"content": "political opinion", "content_type": "text", "metadata": {}}),
        ]
        for name, ctx in contexts:
            times = []
            for _ in range(100):
                start = time.perf_counter()
                await mod_agent.process(ctx)
                times.append((time.perf_counter() - start) * 1000)
            results.append(
                BenchmarkResult(
                    name=f"agent_{name}",
                    category="Agent",
                    metrics=_stats(times),
                    raw_data=times,
                )
            )
    except (ImportError, ModuleNotFoundError) as e:
        print(f"  Skipping auto_moderator: {e}")

    return results


# ============================================================================
# Concurrent Benchmarks
# ============================================================================


async def benchmark_concurrent_requests() -> list[BenchmarkResult]:
    """Benchmark concurrent request handling."""
    results = []

    # Concurrent health checks
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        start = time.perf_counter()
        tasks = [client.get("/health") for _ in range(100)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = (time.perf_counter() - start) * 1000

    successful = sum(1 for r in responses if not isinstance(r, Exception))
    results.append(
        BenchmarkResult(
            name="concurrent_health_100",
            category="Concurrent",
            metrics={
                "total_ms": round(total_time, 2),
                "successful": successful,
                "failed": 100 - successful,
                "rps": round(successful / (total_time / 1000), 2),
            },
        )
    )

    # Concurrent mixed requests
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        start = time.perf_counter()
        tasks = []
        for i in range(50):
            if i % 3 == 0:
                tasks.append(client.get("/health"))
            elif i % 3 == 1:
                tasks.append(client.get("/communities"))
            else:
                tasks.append(client.get("/members"))
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = (time.perf_counter() - start) * 1000

    successful = sum(1 for r in responses if not isinstance(r, Exception))
    results.append(
        BenchmarkResult(
            name="concurrent_mixed_50",
            category="Concurrent",
            metrics={
                "total_ms": round(total_time, 2),
                "successful": successful,
                "failed": 50 - successful,
                "rps": round(successful / (total_time / 1000), 2),
            },
        )
    )

    return results


# ============================================================================
# Report Generation
# ============================================================================


def identify_bottlenecks(results: list[BenchmarkResult]) -> list[dict[str, Any]]:
    """Identify performance bottlenecks from benchmark results."""
    bottlenecks = []

    # Thresholds for bottleneck identification
    thresholds = {
        "API": {"avg_ms": 100, "p95_ms": 200},
        "Database": {"avg_ms": 50, "p95_ms": 100},
        "Agent": {"avg_ms": 100, "p95_ms": 200},
        "Concurrent": {"avg_ms": 500, "p95_ms": 1000},
    }

    for result in results:
        category = result.category
        if category not in thresholds:
            continue
        threshold = thresholds[category]
        metrics = result.metrics

        if "avg_ms" in metrics:
            if metrics["avg_ms"] > threshold["avg_ms"]:
                bottlenecks.append(
                    {
                        "name": result.name,
                        "category": category,
                        "severity": "high" if metrics["avg_ms"] > threshold["avg_ms"] * 2 else "medium",
                        "metric": "avg_ms",
                        "value": metrics["avg_ms"],
                        "threshold": threshold["avg_ms"],
                        "recommendation": _get_recommendation(result.name, "avg_ms"),
                    }
                )
            if "p95_ms" in metrics and metrics["p95_ms"] > threshold["p95_ms"]:
                bottlenecks.append(
                    {
                        "name": result.name,
                        "category": category,
                        "severity": "high" if metrics["p95_ms"] > threshold["p95_ms"] * 2 else "medium",
                        "metric": "p95_ms",
                        "value": metrics["p95_ms"],
                        "threshold": threshold["p95_ms"],
                        "recommendation": _get_recommendation(result.name, "p95_ms"),
                    }
                )

    return bottlenecks


def _get_recommendation(name: str, metric: str) -> str:
    """Get optimization recommendation for a bottleneck."""
    recommendations = {
        "api": "Consider adding caching, optimizing database queries, or using async endpoints.",
        "db": "Consider adding indexes, optimizing queries, or using connection pooling.",
        "agent": "Consider caching results, optimizing algorithms, or using faster models.",
        "concurrent": "Consider increasing worker count, using connection pooling, or optimizing resource usage.",
    }
    for key, rec in recommendations.items():
        if key in name.lower():
            return rec
    return "Review and optimize the implementation."


def generate_report(results: list[BenchmarkResult], bottlenecks: list[dict]) -> str:
    """Generate markdown report from benchmark results."""
    lines = [
        "# Gated Communities — Performance Benchmark Report",
        "",
        f"**Date:** {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
        "",
        "## Summary",
        "",
    ]

    # Group by category
    categories: dict[str, list[BenchmarkResult]] = {}
    for r in results:
        categories.setdefault(r.category, []).append(r)

    for category, cat_results in categories.items():
        lines.append(f"## {category} Performance")
        lines.append("")
        lines.append("| Benchmark | Avg (ms) | Min (ms) | Max (ms) | P95 (ms) | P99 (ms) |")
        lines.append("|-----------|----------|----------|----------|----------|----------|")
        for r in cat_results:
            m = r.metrics
            lines.append(
                f"| {r.name} | {m.get('avg_ms', 'N/A')} | {m.get('min_ms', 'N/A')} | "
                f"{m.get('max_ms', 'N/A')} | {m.get('p95_ms', 'N/A')} | {m.get('p99_ms', 'N/A')} |"
            )
        lines.append("")

    # Bottlenecks
    if bottlenecks:
        lines.append("## Identified Bottlenecks")
        lines.append("")
        lines.append("| Benchmark | Category | Severity | Metric | Value (ms) | Threshold (ms) | Recommendation |")
        lines.append("|-----------|----------|----------|--------|------------|----------------|----------------|")
        for b in bottlenecks:
            lines.append(
                f"| {b['name']} | {b['category']} | {b['severity']} | {b['metric']} | "
                f"{b['value']} | {b['threshold']} | {b['recommendation']} |"
            )
        lines.append("")
    else:
        lines.append("## Bottlenecks")
        lines.append("")
        lines.append("No significant bottlenecks identified.")
        lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")
    lines.append("1. **Database**: Add indexes on frequently queried columns (tier_id, is_private, community_id).")
    lines.append("2. **API**: Implement caching for read-heavy endpoints.")
    lines.append("3. **Agents**: Cache agent results for repeated inputs.")
    lines.append("4. **Concurrent**: Use connection pooling and async database drivers.")
    lines.append("")

    return "\n".join(lines)


async def main() -> None:
    """Run all benchmarks and generate report."""
    print("Running Gated Communities Performance Benchmarks...")
    print("=" * 60)

    # Import here to avoid issues with test fixtures
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from gated_communities.main import app
    from gated_communities.database import Base, get_db
    from gated_communities.auth import register_user

    # Setup test database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Populate test data
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()

    from gated_communities.models import (
        AuditLog,
        Community,
        CommunityStatus,
        CommunityTier,
        Member,
        MemberRole,
        ModerationItem,
    )

    communities = []
    for i in range(50):
        c = Community(
            name=f"Community {i}",
            description=f"Description for community {i}",
            tier=[CommunityTier.FREE, CommunityTier.BASIC, CommunityTier.PREMIUM, CommunityTier.ENTERPRISE][i % 4],
            status=CommunityStatus.ACTIVE,
        )
        db_session.add(c)
        communities.append(c)
    db_session.flush()

    for i in range(200):
        m = Member(
            community_id=communities[i % 50].id,
            user_id=i + 1,
            role=[MemberRole.MEMBER, MemberRole.MODERATOR, MemberRole.ADMIN][i % 3],
        )
        db_session.add(m)

    for i in range(100):
        mi = ModerationItem(
            community_id=communities[i % 50].id,
            reporter_id=i + 1,
            target_type=["post", "comment", "message"][i % 3],
            target_id=i + 1,
            reason=f"Reason {i}",
            status=["pending", "approved", "rejected"][i % 3],
        )
        db_session.add(mi)

    for i in range(100):
        al = AuditLog(
            community_id=communities[i % 50].id,
            user_id=i + 1,
            action=["create", "update", "delete", "login"][i % 4],
            details=f"Details {i}",
        )
        db_session.add(al)

    db_session.commit()

    # Create test client
    with TestClient(app) as client:
        # Register and login
        register_user("benchuser", "bench@example.com", "benchpass123")
        resp = client.post(
            "/auth/login",
            json={"username": "benchuser", "password": "benchpass123"},
        )
        auth_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

        all_results: list[BenchmarkResult] = []

        # API Benchmarks
        print("\n[1/4] API Benchmarks...")
        api_results = benchmark_api_endpoints(client)
        all_results.extend(api_results)
        for r in api_results:
            print(f"  {r.name}: {r.metrics.get('avg_ms', 'N/A')}ms avg")

        api_auth_results = benchmark_api_authenticated(client, auth_headers)
        all_results.extend(api_auth_results)
        for r in api_auth_results:
            print(f"  {r.name}: {r.metrics.get('avg_ms', 'N/A')}ms avg")

        api_write_results = benchmark_api_writes(client, auth_headers)
        all_results.extend(api_write_results)
        for r in api_write_results:
            print(f"  {r.name}: {r.metrics.get('avg_ms', 'N/A')}ms avg")

        # Database Benchmarks
        print("\n[2/4] Database Benchmarks...")
        db_results = benchmark_database_queries(db_session)
        all_results.extend(db_results)
        for r in db_results:
            print(f"  {r.name}: {r.metrics.get('avg_ms', 'N/A')}ms avg")

        orm_results = benchmark_database_orm(db_session)
        all_results.extend(orm_results)
        for r in orm_results:
            print(f"  {r.name}: {r.metrics.get('avg_ms', 'N/A')}ms avg")

        # Agent Benchmarks
        print("\n[3/4] Agent Benchmarks...")
        agent_results = await benchmark_agents()
        all_results.extend(agent_results)
        for r in agent_results:
            print(f"  {r.name}: {r.metrics.get('avg_ms', 'N/A')}ms avg")

        # Concurrent Benchmarks
        print("\n[4/4] Concurrent Benchmarks...")
        concurrent_results = await benchmark_concurrent_requests()
        all_results.extend(concurrent_results)
        for r in concurrent_results:
            print(f"  {r.name}: {r.metrics.get('rps', 'N/A')} req/s")

    # Identify bottlenecks
    bottlenecks = identify_bottlenecks(all_results)

    # Generate report
    report = generate_report(all_results, bottlenecks)

    # Save results
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "results": [
            {
                "name": r.name,
                "category": r.category,
                "metrics": r.metrics,
            }
            for r in all_results
        ],
        "bottlenecks": bottlenecks,
    }

    results_file = RESULTS_DIR / "benchmark_results.json"
    results_file.write_text(json.dumps(output, indent=2))
    print(f"\nResults saved to: {results_file}")

    report_file = RESULTS_DIR / "benchmark_report.md"
    report_file.write_text(report)
    print(f"Report saved to: {report_file}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for category in ["API", "Database", "Agent", "Concurrent"]:
        cat_results = [r for r in all_results if r.category == category]
        if cat_results:
            avg_times = [r.metrics.get("avg_ms", 0) for r in cat_results if "avg_ms" in r.metrics]
            if avg_times:
                print(f"{category}: {statistics.mean(avg_times):.2f}ms avg")

    if bottlenecks:
        print(f"\n{len(bottlenecks)} bottleneck(s) identified:")
        for b in bottlenecks:
            print(f"  - {b['name']}: {b['metric']}={b['value']}ms (threshold: {b['threshold']}ms)")
    else:
        print("\nNo significant bottlenecks identified.")


if __name__ == "__main__":
    asyncio.run(main())
