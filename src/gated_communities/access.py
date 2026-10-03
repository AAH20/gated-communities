"""Access control and request management."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .community import Community
    from .gate import Gate


class AccessDecision(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"
    REVOKED = "revoked"


@dataclass
class AccessRequest:
    """A request to access a community."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    community_id: str = ""
    context: dict = field(default_factory=dict)
    decision: AccessDecision = AccessDecision.PENDING
    reason: str = ""
    requested_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    resolved_by: str | None = None


@dataclass
class AccessController:
    """Controls access to gated communities."""

    def evaluate_access(
        self,
        user_id: str,
        community: Community,
        gate: Gate,
        context: dict | None = None,
    ) -> AccessRequest:
        """Evaluate whether a user can access a community."""
        ctx = context or {}

        # Check if community allows joining
        if not community.can_join(user_id):
            return AccessRequest(
                user_id=user_id,
                community_id=community.id,
                context=ctx,
                decision=AccessDecision.DENIED,
                reason="Community is full or inactive",
            )

        # Evaluate gate rules
        passed, failed_rules = gate.evaluate(ctx)
        if not passed:
            return AccessRequest(
                user_id=user_id,
                community_id=community.id,
                context=ctx,
                decision=AccessDecision.DENIED,
                reason=f"Failed gate rules: {', '.join(failed_rules)}",
            )

        # Check if approval is required
        if community.config.require_approval:
            return AccessRequest(
                user_id=user_id,
                community_id=community.id,
                context=ctx,
                decision=AccessDecision.PENDING,
                reason="Approval required",
            )

        return AccessRequest(
            user_id=user_id,
            community_id=community.id,
            context=ctx,
            decision=AccessDecision.GRANTED,
            reason="Access granted",
        )

    def approve_request(
        self,
        request: AccessRequest,
        approved_by: str,
    ) -> AccessRequest:
        """Approve a pending access request."""
        request.decision = AccessDecision.GRANTED
        request.resolved_at = datetime.utcnow()
        request.resolved_by = approved_by
        request.reason = "Access approved"
        return request

    def deny_request(
        self,
        request: AccessRequest,
        denied_by: str,
        reason: str = "",
    ) -> AccessRequest:
        """Deny a pending access request."""
        request.decision = AccessDecision.DENIED
        request.resolved_at = datetime.utcnow()
        request.resolved_by = denied_by
        request.reason = reason or "Access denied"
        return request
