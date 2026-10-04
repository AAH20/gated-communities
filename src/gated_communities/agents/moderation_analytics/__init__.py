"""Base agent class for moderation analytics agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import structlog

from .analytics_explainer import AnalyticsExplainerAgent
from .moderation_predictor import ModerationPredictorAgent
from .moderator_performance import ModeratorPerformanceAgent
from .policy_effectiveness import PolicyEffectivenessAgent
from .trend_analyzer import TrendAnalyzerAgent

try:
    from langchain_openai import ChatOpenAI
    from .config import get_settings
except ImportError:
    ChatOpenAI = None
    get_settings = None

if TYPE_CHECKING:
    from langchain_core.language_models import BaseLanguageModel

logger = structlog.get_logger(__name__)

T = TypeVar("T")

__all__ = [
    "BaseAgent",
    "AnalyticsExplainerAgent",
    "ModerationPredictorAgent",
    "ModeratorPerformanceAgent",
    "PolicyEffectivenessAgent",
    "TrendAnalyzerAgent",
]


class BaseAgent(ABC, Generic[T]):
    """Abstract base class for all moderation analytics agents."""

    def __init__(self, name: str, llm: BaseLanguageModel | None = None) -> None:
        self.name = name
        self.logger = logger.bind(agent=name)
        self._llm = llm
        self._settings = get_settings() if get_settings else None

    @property
    def llm(self):
        if self._llm is None and ChatOpenAI:
            self._llm = ChatOpenAI(
                model=self._settings.langchain_model if self._settings else "gpt-4o-mini",
                temperature=self._settings.langchain_temperature if self._settings else 0.1,
                max_tokens=self._settings.langchain_max_tokens if self._settings else 1000,
            )
        return self._llm

    async def run(self, **kwargs: Any) -> T:
        raise NotImplementedError("Subclasses must implement run()")
