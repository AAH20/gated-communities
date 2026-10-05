"""Main application entry point with health checks and route registration."""
from fastapi import FastAPI



# --- Already registered routers ---

# Every (module, router attribute) pair that register_all_routers tries to
# mount. Module-level so tests can assert full mount accounting.
ROUTER_REGISTRY: tuple[tuple[str, str], ...] = (
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

#: Base routers mounted directly by ``gated_communities.main`` before
#: register_all_routers runs. register_all_routers must mount more than these.
BASE_ROUTER_MODULES: frozenset[str] = frozenset(
    {
        "health",
        "communities",
        "members",
        "moderation",
        "search",
        "audit",
        "export",
        "bulk",
        "websocket",
    }
)

#: Routers whose endpoints must always be reachable. A skip here means a real
#: outage, so these are asserted individually rather than just counted.
REQUIRED_ROUTERS: tuple[str, ...] = (
    "health",
    "communities",
    "members",
    "moderation",
    "tiers",
)


def register_all_routers(target: FastAPI) -> dict[str, str]:
    """Register every API router on ``target``.

    Each router is imported lazily and individually so that one broken module
    (a router whose agent dependency was never implemented) cannot prevent the
    rest of the API from mounting.

    Skipping is deliberately *not* silent: every failure is logged at WARNING
    with a greppable ``ROUTER_MOUNT_SKIPPED`` marker, and the ``module.attr``
    keys are recorded on ``target.state.skipped_routers``. Downstream code and
    tests read that state to assert no router silently disappeared.

    Returns the ``{module.attr: reason}`` mapping that is also stored on
    ``target.state.skipped_routers``.
    """
    import importlib
    import logging

    log = logging.getLogger(__name__)

    skipped: dict[str, str] = {}

    def _skip(module_name: str, router_attr: str, reason: str) -> None:
        key = f"{module_name}.{router_attr}"
        skipped[key] = reason
        # ROUTER_MOUNT_SKIPPED is greppable in CI logs.
        log.warning("ROUTER_MOUNT_SKIPPED %s: %s", key, reason)

    for module_name, router_attr in ROUTER_REGISTRY:
        try:
            module = importlib.import_module(f"{__package__}.{module_name}")
            router = getattr(module, router_attr)
        except (ImportError, AttributeError) as exc:
            _skip(module_name, router_attr, f"{type(exc).__name__}: {exc}")
            continue
        try:
            target.include_router(router)
        except Exception as exc:  # pragma: no cover - defensive
            # Routers that declare a root path with no prefix cannot be mounted.
            _skip(module_name, router_attr, f"{type(exc).__name__}: {exc}")

    # Expose the skips so CI/tests can assert nothing vanished unnoticed.
    target.state.skipped_routers = skipped
    return skipped
