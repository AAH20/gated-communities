"""Configuration module for community governance."""

from .community_governance_logging_config import get_logger, setup_logging
from .community_governance_settings import Settings, get_settings

__all__ = ["Settings", "get_logger", "get_settings", "setup_logging"]
