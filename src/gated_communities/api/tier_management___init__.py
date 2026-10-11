"""API route modules for tier management."""

from __future__ import annotations

from fastapi import APIRouter
from ..api.access import access_router
from ..api.analytics import analytics_router
from ..api.benefits import benefits_router
from ..api.evaluation import evaluation_router
from ..api.health import health_router
from ..api.tiers import tiers_router
from ..api.upgrades import upgrades_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(tiers_router, prefix="/tiers", tags=["tiers"])
router.include_router(access_router, prefix="/access", tags=["access"])
router.include_router(benefits_router, prefix="/benefits", tags=["benefits"])
router.include_router(evaluation_router, prefix="/evaluation", tags=["evaluation"])
router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
router.include_router(upgrades_router, prefix="/upgrades", tags=["upgrades"])

__all__ = ["router"]
