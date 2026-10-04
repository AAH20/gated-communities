"""
Agents module - Contains all AI agents for gated community management.

Each sub-package corresponds to a specific domain:
- tier_management: Tier evaluation, benefits, upgrades
- moderation_queue: Auto-moderation, queue optimization, escalation
- access_control: Permission evaluation, role management, policy enforcement
- community_health_scorer: Toxicity detection, engagement metrics
- member_verification: Identity verification, fraud prevention, trust scoring
- escalation_workflow: Auto-resolution, SLA tracking, priority routing
- reputation_system: Reputation scoring, badges, trust tiers
- compliance_monitor: Policy tracking, violation detection, audits
- moderation-analytics: Trend analysis, predictor, performance metrics
- community_governance: Dispute resolution, rule enforcement, policy management
"""

# Optional imports that may require additional dependencies
try:
    from . import access_control
except ImportError:
    access_control = None

try:
    from . import community_governance
except ImportError:
    community_governance = None

try:
    from . import community_health_scorer
except ImportError:
    community_health_scorer = None

try:
    from . import compliance_monitor
except ImportError:
    compliance_monitor = None

try:
    from . import escalation_workflow
except ImportError:
    escalation_workflow = None

try:
    from . import member_verification
except ImportError:
    member_verification = None

try:
    from . import moderation_analytics
except ImportError:
    moderation_analytics = None

try:
    from . import moderation_queue
except ImportError:
    moderation_queue = None

try:
    from . import reputation_system
except ImportError:
    reputation_system = None

try:
    from . import tier_management
except ImportError:
    tier_management = None

__all__ = [
    "access_control",
    "community_governance",
    "community_health_scorer",
    "compliance_monitor",
    "escalation_workflow",
    "member_verification",
    "moderation_analytics",
    "moderation_queue",
    "reputation_system",
    "tier_management",
]
