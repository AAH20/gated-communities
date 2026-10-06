"""API dependencies for community governance."""

from __future__ import annotations

from typing import Any

from ..agents.community_governance import (
    DisputeResolverAgent,
    GovernanceAnalyticsAgent,
    GovernanceExplainerAgent,
    PolicyManagerAgent,
    RuleEnforcerAgent,
)
from ..integrations.community_governance___init__ import MetricsIntegration

# Global agent instances (initialized in main.py)
_agents: dict[str, Any] = {}
_metrics: MetricsIntegration | None = None


def set_agents(agents: dict[str, Any]) -> None:
    """Set the global agent instances.

    Args:
        agents: Dictionary of agent instances.
    """
    global _agents
    _agents = agents


def get_agents() -> dict[str, Any]:
    """Get the global agent instances.

    Returns:
        Dictionary of agent instances.
    """
    return _agents


def _resolve(key: str, factory: type) -> Any:
    """Return a registered agent, constructing a default one if absent.

    The dedicated ``community_governance`` app registers agents via
    :func:`set_agents` during startup. When these routers are mounted on the
    unified API that bootstrap never runs, so fall back to a default-constructed
    agent rather than raising ``KeyError``.

    Args:
        key: Registry key for the agent.
        factory: Agent class used to build a default instance.

    Returns:
        The registered or default-constructed agent instance.
    """
    agent = _agents.get(key)
    if agent is None:
        agent = factory()
        _agents[key] = agent
    return agent


def get_rule_enforcer() -> RuleEnforcerAgent:
    """Get the rule enforcer agent.

    Returns:
        The rule enforcer agent instance.
    """
    return _resolve("rule_enforcer", RuleEnforcerAgent)


def get_dispute_resolver() -> DisputeResolverAgent:
    """Get the dispute resolver agent.

    Returns:
        The dispute resolver agent instance.
    """
    return _resolve("dispute_resolver", DisputeResolverAgent)


def get_policy_manager() -> PolicyManagerAgent:
    """Get the policy manager agent.

    Returns:
        The policy manager agent instance.
    """
    return _resolve("policy_manager", PolicyManagerAgent)


def get_governance_analytics() -> GovernanceAnalyticsAgent:
    """Get the governance analytics agent.

    Returns:
        The governance analytics agent instance.
    """
    return _resolve("governance_analytics", GovernanceAnalyticsAgent)


def get_governance_explainer() -> GovernanceExplainerAgent:
    """Get the governance explainer agent.

    Returns:
        The governance explainer agent instance.
    """
    return _resolve("governance_explainer", GovernanceExplainerAgent)


def set_metrics(metrics: MetricsIntegration) -> None:
    """Set the global metrics integration.

    Args:
        metrics: The metrics integration instance.
    """
    global _metrics
    _metrics = metrics


def get_metrics() -> MetricsIntegration:
    """Get the global metrics integration.

    Returns:
        The metrics integration instance.
    """
    global _metrics

    if _metrics is None:
        _metrics = MetricsIntegration()
    return _metrics
