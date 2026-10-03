"""Test configuration and fixtures."""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from gated_communities.main import app
from gated_communities.database import Base, get_db
from gated_communities.auth import register_user, create_access_token
from gated_communities.rate_limit import rate_limiter


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable foreign key enforcement for SQLite
from sqlalchemy import event
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
    # Register a test user
    register_user("testuser", "test@example.com", "testpass123")
    # Login to get token
    resp = client.post("/auth/login", json={"username": "testuser", "password": "testpass123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_community():
    return {
        "name": "Test Community",
        "description": "A test community",
        "is_private": False,
        "tier_id": "free",
        "capacity": 100,
    }


@pytest.fixture
def sample_member():
    return {
        "email": "test@example.com",
        "name": "Test User",
        "role": "member",
        "community_id": 1,
    }
