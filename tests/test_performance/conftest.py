"""Shared fixtures for performance benchmarks."""

from __future__ import annotations

import statistics
import time
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from gated_communities.main import app
from gated_communities.database import Base, get_db
from gated_communities.auth import register_user, create_access_token
from gated_communities.rate_limit import rate_limiter

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
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


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state before each test."""
    rate_limiter.reset()
    yield
    rate_limiter.reset()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with fresh database."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Create a test user and return auth headers."""
    # Use a unique username per test to avoid conflicts
    import uuid
    username = f"perfuser_{uuid.uuid4().hex[:8]}"
    register_user(username, f"{username}@example.com", "perfpass123")
    resp = client.post(
        "/auth/login", json={"username": username, "password": "perfpass123"}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def populated_db(db_session):
    """Populate the database with test data for benchmarking."""
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

    members = []
    for i in range(200):
        m = Member(
            community_id=communities[i % 50].id,
            user_id=i + 1,
            role=[MemberRole.MEMBER, MemberRole.MODERATOR, MemberRole.ADMIN][i % 3],
        )
        db_session.add(m)
        members.append(m)

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
    return db_session


def run_benchmark(
    func: Callable[[], Any],
    iterations: int = 50,
    warmup: int = 5,
) -> dict[str, Any]:
    """Run a benchmark function and return timing statistics.

    Args:
        func: The function to benchmark.
        iterations: Number of iterations to run.
        warmup: Number of warmup iterations (not counted).

    Returns:
        Dictionary with timing statistics in milliseconds.
    """
    # Warmup
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


def run_async_benchmark(
    func: Callable[[], Any],
    iterations: int = 50,
    warmup: int = 5,
) -> dict[str, Any]:
    """Run an async benchmark function and return timing statistics."""
    import asyncio

    async def _run():
        # Warmup
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

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're inside an async test - create a new loop in a thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, _run()).result()
    else:
        return asyncio.run(_run())
