"""API route aggregators."""

from .agents import router as agents_router
from .escalations import router as escalations_router
from .items import router as items_router
from .queues import router as queues_router
from .reviews import router as reviews_router

__all__ = [
    "agents_router",
    "escalations_router",
    "items_router",
    "queues_router",
    "reviews_router",
]
