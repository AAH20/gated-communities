# Gated Communities — Documentation

Gated Communities is a **Python / FastAPI** platform for gated *online
communities* — tier management, moderation queue, access control, member
verification, reputation, compliance, and governance. It is **not** a Node.js
resident/visitor/amenity platform.

The authoritative project overview and quick start live in
[`../README.md`](../README.md).

## What this project actually is

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Framework | FastAPI + Uvicorn |
| Validation | Pydantic v2 |
| Database | SQLAlchemy 2.0 — SQLite by default (`src/gated_communities/config/__init__.py`) |
| Cache | In-process (pluggable) — no Redis required |
| Tests | pytest (`tests/`) |
| Deploy | Docker + Helm + Kubernetes; CD gated on the `DEPLOY_ENABLED` repo variable |

## Entrypoint & routing

```bash
# Application entrypoint used by the Dockerfile and docker-compose
uvicorn gated_communities.main:app --reload --port 8000
```

Routers are mounted at the app **root** (e.g. `/tiers`, `/communities`,
`/members`) — there is **no** global `/api/v1` prefix. A few legacy routers do
still expose an `/api/v1/...` segment (e.g. `/api/v1/access/check`,
`/api/v1/disputes`).

## Health endpoints

```bash
curl http://localhost:8000/health        # overall health
curl http://localhost:8000/health/ready  # readiness probe
curl http://localhost:8000/ready         # readiness probe
curl http://localhost:8000/live          # liveness probe
```

## Documentation index

| Document | Description |
|----------|-------------|
| [../README.md](../README.md) | Project overview, features, API summary |
| [API.md](./API.md) | REST API reference |
| [api-reference.md](./api-reference.md) | Extended endpoint specifications |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Deployment guide |
| [deployment-guide.md](./deployment-guide.md) | Kubernetes-oriented deployment guide |
| [development-guide.md](./development-guide.md) | Local development workflow |
| [architecture.md](./architecture.md) | Architecture overview |
| [user-guide.md](./user-guide.md) | End-user guide |
| [FAQ.md](./FAQ.md) | Frequently asked questions |
| [WEBHOOKS.md](./WEBHOOKS.md) | Webhook integration notes |
| [SDK.md](./SDK.md) | Python SDK notes |
