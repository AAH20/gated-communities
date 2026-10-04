"""Main application entry point with health checks and route registration."""
from fastapi import FastAPI

from . import (
    access,
    access_control_routes,
    agents,
    analytics,
    audit,
    audits,
    badges,
    benefits,
    bulk,
    comments,
    communities,
    community_governance_analytics,
    community_governance_health,
    community_governance_policies,
    disputes,
    documents,
    escalation_workflow_escalations,
    escalation_workflow_health,
    escalations,
    evaluation,
    events,
    explain,
    explanations,
    export,
    fraud,
    health,
    history,
    invitations,
    items,
    member_verification_agents,
    member_verification_health,
    members,
    messages,
    metrics,
    moderation,
    moderation_queue_routes,
    policies,
    posts,
    priorities,
    queues,
    remediation,
    reports,
    reputation,
    reputation_system_health,
    resolutions,
    reviews,
    rules,
    scores,
    search,
    settings,
    sla,
    tiers,
    trust,
    trust_tiers,
    upgrades,
    verification,
    violations,
    webhooks,
    websocket,
    websockets,
)

app = FastAPI(title="Gated Communities API", version="1.0.0")

# --- Already registered routers ---
app.include_router(moderation.router)
app.include_router(export.router)
app.include_router(search.router)
app.include_router(audit.router)

# --- Newly registered orphaned routers ---
app.include_router(access.access_router)
app.include_router(access_control_routes.router)
app.include_router(agents.router)
app.include_router(analytics.analytics_router)
app.include_router(audits.router)
app.include_router(badges.router)
app.include_router(benefits.benefits_router)
app.include_router(bulk.router)
app.include_router(comments.router)
app.include_router(communities.router)
app.include_router(community_governance_analytics.router)
app.include_router(community_governance_health.router)
app.include_router(community_governance_policies.router)
app.include_router(disputes.router)
app.include_router(documents.router)
app.include_router(escalation_workflow_escalations.router)
app.include_router(escalation_workflow_health.router)
app.include_router(escalations.router)
app.include_router(evaluation.evaluation_router)
app.include_router(events.router)
app.include_router(explain.router)
app.include_router(explanations.router)
app.include_router(fraud.router)
app.include_router(health.health_router)
app.include_router(history.router)
app.include_router(invitations.router)
app.include_router(items.router)
app.include_router(member_verification_agents.router)
app.include_router(member_verification_health.router)
app.include_router(members.router)
app.include_router(messages.router)
app.include_router(metrics.router)
app.include_router(moderation_queue_routes.router)
app.include_router(policies.router)
app.include_router(posts.router)
app.include_router(priorities.router)
app.include_router(queues.router)
app.include_router(remediation.router)
app.include_router(reports.router)
app.include_router(reputation.router)
app.include_router(reputation_system_health.router)
app.include_router(resolutions.router)
app.include_router(reviews.router)
app.include_router(rules.router)
app.include_router(scores.router)
app.include_router(settings.router)
app.include_router(sla.router)
app.include_router(tiers.tiers_router)
app.include_router(trust.router)
app.include_router(trust_tiers.router)
app.include_router(upgrades.upgrades_router)
app.include_router(verification.router)
app.include_router(violations.router)
app.include_router(webhooks.router)
app.include_router(websocket.router)
app.include_router(websockets.router)


@app.get("/ready")
async def readiness_check() -> dict[str, str]:
    """Readiness probe for orchestration."""
    return {"status": "ready"}


@app.get("/live")
async def liveness_check() -> dict[str, str]:
    """Liveness probe for orchestration."""
    return {"status": "alive"}
