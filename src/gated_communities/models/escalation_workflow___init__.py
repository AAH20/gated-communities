"""Pydantic models for escalation workflow entities."""

from .analysis import EscalationAnalysis, EscalationPattern
from .escalation import (
    Escalation,
    EscalationCreate,
    EscalationStatus,
    EscalationUpdate,
)
from .priority import Priority, PriorityLevel
from .resolution import Resolution, ResolutionCreate, ResolutionStatus
from .sla import SLA, SLABreach, SLAStatus

__all__ = [
    "Escalation",
    "EscalationCreate",
    "EscalationStatus",
    "EscalationUpdate",
    "Priority",
    "PriorityLevel",
    "SLA",
    "SLABreach",
    "SLAStatus",
    "Resolution",
    "ResolutionCreate",
    "ResolutionStatus",
    "EscalationAnalysis",
    "EscalationPattern",
]
