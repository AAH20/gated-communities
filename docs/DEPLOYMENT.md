# Deployment Guide — Gated Communities

Gated Communities is a Python/FastAPI application. Everything needed to build and
run it (Dockerfile, docker-compose, Helm chart, k8s manifests) ships in the repo.

## Container image

```bash
docker build -t gated-communities:local .
docker run -p 8000:8000 gated-communities:local
curl http://localhost:8000/health
```

The image runs `uvicorn gated_communities.main:app` on port `8000`.

## Docker Compose

```bash
docker compose up -d     # app, db (optional), redis (optional), nginx
```

The `app` service defaults to SQLite (`DATABASE_URL=sqlite:///./gated_communities.db`);
`db`/`redis` are optional.

## Kubernetes

```bash
kubectl apply -f k8s/
# or
helm install gated-communities ./helm/
```

Probes use `/health` (see `k8s/deployment.yaml`).

## Health endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Overall health |
| `GET /health/ready` | Readiness |
| `GET /ready` | Readiness |
| `GET /live` | Liveness |

## Continuous Delivery (GitHub Actions)

`.github/workflows/deploy.yml` builds and pushes the image, then deploys to
staging and production. **Deploys are gated on the repository variable
`DEPLOY_ENABLED`:** the `deploy-staging`, `smoke-tests`, and `deploy-production`
jobs run only when `vars.DEPLOY_ENABLED == 'true'`. Until it is set, the workflow
builds and pushes and finishes green without deploying.

`STAGING_HOST` and `PRODUCTION_HOST` are **placeholder example domains** and the
deploy steps are stubs — provide real infrastructure before enabling the gate.
