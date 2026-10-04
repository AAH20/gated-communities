"""
Configuration module - Settings, logging, and environment configuration.
"""

__all__ = []

"""Application configuration."""

import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gated_communities.db")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_gated_communities.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
MAX_COMMUNITIES_PER_TIER = {"free": 3, "pro": 10, "enterprise": -1}
MAX_MEMBERS_PER_TIER = {"free": 100, "pro": 1000, "enterprise": -1}
