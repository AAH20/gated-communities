"""Gate module."""

from __future__ import annotations
from enum import StrEnum
from typing import Any


class GateType(StrEnum):
    """Gate type."""
    TIER = "tier"
    ROLE = "role"
    CUSTOM = "custom"


class GateRule:
    """Gate rule."""
    def __init__(self, gate_type: GateType, **kwargs):
        self.gate_type = gate_type
        self.config = kwargs


class Gate:
    """Gate."""
    def __init__(self, name: str, rules: list[GateRule] | None = None):
        self.name = name
        self.rules = rules or []

    def evaluate(self, context: dict[str, Any]) -> bool:
        return True
