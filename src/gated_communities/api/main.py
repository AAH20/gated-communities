"""Main application entry point with health checks and route registration."""
from fastapi import FastAPI



# --- Already registered routers ---


def register_all_routers(target: FastAPI) -> None:
    """Register every API router on ``target``.

    Each router is imported lazily and individually so that one broken module
    (a router whose agent dependency was never implemented) cannot prevent the
    rest of the API from mounting. Broken routers are reported once via the
    application logger and skipped.
    """
    import importlib
    import logging

    log = logging.getLogger(__name__)

    _REGISTRY: tuple[tuple[str, str], ...] = (
        ("moderation", "router"),
        ("export", "router"),
        ("search", "router"),
        ("audit", "router"),
        ("access", "access_router"),
        ("access_control_routes", "router"),
        ("agents", "router"),
        ("analytics", "analytics_router"),
        ("audits", "router"),
        ("badges", "router"),
        ("benefits", "benefits_router"),
        ("bulk", "router"),
        ("comments", "router"),
        ("communities", "router"),
        ("community_governance_analytics", "router"),
        ("community_governance_health", "router"),
        ("community_governance_policies", "router"),
        ("disputes", "router"),
        ("documents", "router"),
        ("escalation_workflow_escalations", "router"),
        ("escalation_workflow_health", "router"),
        ("escalations", "router"),
        ("evaluation", "evaluation_router"),
        ("events", "router"),
        ("explain", "router"),
        ("explanations", "router"),
        ("fraud", "router"),
        ("health", "health_router"),
        ("history", "router"),
        ("invitations", "router"),
        ("items", "router"),
        ("member_verification_agents", "router"),
        ("member_verification_health", "router"),
        ("members", "router"),
        ("messages", "router"),
        ("metrics", "router"),
        ("moderation_queue_routes", "router"),
        ("policies", "router"),
        ("posts", "router"),
        ("priorities", "router"),
        ("queues", "router"),
        ("remediation", "router"),
        ("reports", "router"),
        ("reputation", "router"),
        ("reputation_system_health", "router"),
        ("resolutions", "router"),
        ("reviews", "router"),
        ("rules", "router"),
        ("scores", "router"),
        ("settings", "router"),
        ("sla", "router"),
        ("tiers", "tiers_router"),
        ("trust", "router"),
        ("trust_tiers", "router"),
        ("upgrades", "upgrades_router"),
        ("verification", "router"),
        ("violations", "router"),
        ("webhooks", "router"),
        ("websocket", "router"),
        ("websockets", "router"),
    )

    for module_name, router_attr in _REGISTRY:
        try:
            module = importlib.import_module(f"{__package__}.{module_name}")
            router = getattr(module, router_attr)
        except (ImportError, AttributeError) as exc:
            log.warning(
                "Skipping router %s.%s: %s", module_name, router_attr, exc
            )
            continue
        try:
            target.include_router(router)
        except Exception as exc:  # pragma: no cover - defensive
            # Routers that declare a root path with no prefix cannot be mounted.
            log.warning(
                "Skipping router %s.%s: %s", module_name, router_attr, exc
            )
