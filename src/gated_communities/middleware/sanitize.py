"""Sanitize middleware."""

from __future__ import annotations


def sanitize_string(value: str) -> str:
    """Sanitize a string value."""
    return value.strip()
