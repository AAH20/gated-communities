"""Base declarative class for SQLAlchemy models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all models."""
