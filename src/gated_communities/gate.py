"""Gate rules for community access control."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class GateType(str, Enum):
    """Types of access gates."""

    INVITE_ONLY = "invite_only"
    PAYMENT = "payment"
    APPLICATION = "application"
    DOMAIN_WHITELIST = "domain_whitelist"
    TOKEN_GATE = "token_gate"
    NFT_GATE = "nft_gate"
    CUSTOM = "custom"


@dataclass
class GateRule:
    """A single gate rule."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    gate_type: GateType = GateType.CUSTOM
    name: str = ""
    description: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate the gate rule against a context."""
        if not self.is_active:
            return True

        evaluators: dict[GateType, Callable[[dict[str, Any]], bool]] = {
            GateType.INVITE_ONLY: self._eval_invite_only,
            GateType.PAYMENT: self._eval_payment,
            GateType.APPLICATION: self._eval_application,
            GateType.DOMAIN_WHITELIST: self._eval_domain_whitelist,
            GateType.TOKEN_GATE: self._eval_token_gate,
            GateType.NFT_GATE: self._eval_nft_gate,
            GateType.CUSTOM: self._eval_custom,
        }

        evaluator = evaluators.get(self.gate_type, self._eval_custom)
        return evaluator(context)

    def _eval_invite_only(self, context: dict[str, Any]) -> bool:
        return context.get("has_invite", False)

    def _eval_payment(self, context: dict[str, Any]) -> bool:
        required_tier = self.config.get("required_tier")
        if not required_tier:
            return True
        user_tier = context.get("payment_tier")
        return user_tier == required_tier

    def _eval_application(self, context: dict[str, Any]) -> bool:
        return context.get("application_approved", False)

    def _eval_domain_whitelist(self, context: dict[str, Any]) -> bool:
        allowed_domains = self.config.get("allowed_domains", [])
        user_email = context.get("email", "")
        if not user_email or "@" not in user_email:
            return False
        domain = user_email.split("@")[1]
        return domain in allowed_domains

    def _eval_token_gate(self, context: dict[str, Any]) -> bool:
        required_token = self.config.get("required_token_address")
        if not required_token:
            return True
        user_tokens = context.get("token_addresses", [])
        return required_token in user_tokens

    def _eval_nft_gate(self, context: dict[str, Any]) -> bool:
        required_collection = self.config.get("required_collection")
        if not required_collection:
            return True
        user_collections = context.get("nft_collections", [])
        return required_collection in user_collections

    def _eval_custom(self, context: dict[str, Any]) -> bool:
        custom_check = self.config.get("custom_check")
        if custom_check and callable(custom_check):
            return custom_check(context)
        return True


@dataclass
class Gate:
    """A collection of gate rules."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    community_id: str = ""
    rules: list[GateRule] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def evaluate(self, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """Evaluate all rules. Returns (passed, failed_rule_names)."""
        failed: list[str] = []
        for rule in sorted(self.rules, key=lambda r: r.priority):
            if not rule.evaluate(context):
                failed.append(rule.name)
        return len(failed) == 0, failed
