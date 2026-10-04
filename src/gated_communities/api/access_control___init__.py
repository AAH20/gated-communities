"""API layer for the access control service."""

from .access_control_dependencies import get_settings
from .access_control_routes import router

__all__ = ["get_settings", "router"]
