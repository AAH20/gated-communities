"""Invitation service."""

from __future__ import annotations
from typing import Any


class InvitationService:
    """Service for managing invitations."""

    def __init__(self, uow=None):
        self._uow = uow

    async def create_invitation(self, community_id: str, email: str) -> dict:
        """Create an invitation."""
        return {"id": "inv-001", "community_id": community_id, "email": email, "status": "pending"}

    async def get_invitation(self, invitation_id: str) -> dict:
        """Get an invitation by ID."""
        return {"id": invitation_id, "status": "pending"}

    async def list_invitations(self, community_id: str) -> list[dict]:
        """List invitations for a community."""
        return []

    async def accept_invitation(self, invitation_id: str) -> dict:
        """Accept an invitation."""
        return {"id": invitation_id, "status": "accepted"}

    async def decline_invitation(self, invitation_id: str) -> dict:
        """Decline an invitation."""
        return {"id": invitation_id, "status": "declined"}
