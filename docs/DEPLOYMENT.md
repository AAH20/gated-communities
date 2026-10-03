# Deployment Guide

This guide covers deploying Gated Communities to production using Docker, Kubernetes, and Terraform.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Terraform Deployment](#terraform-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Migrations](#database-migrations)
- [Health Checks](#health-checks)
- [Monitoring](#monitoring)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Docker 24+ and Docker Compose 2+
- Kubernetes cluster (EKS, GKE, or AKS) 1.28+
- Terraform 1.6+
- Helm 3.13+
- `kubectl` configured for your cluster
- Domain name with DNS management access
- SSL certificate (or cert-manager for automatic provisioning)

---

## Docker Deployment

### Quick Start with Docker Compose

```bash
# Clone the repository
git clone https://github.com/your-org/gated-communities.git
cd gated-communities

# Create environment file
cat > .env <<EOF
PORT=3000
DATABASE_URL=postgresql://postgres:postgres@db:5432/gated_communities
REDIS_URL=redis://redis:6379
JWT_SECRET=your-super-secret-key-change-in-production
JWT_EXPIRY=24h
BCRYPT_ROUNDS=12
RATE_LIMIT_WINDOW=900000
RATE_LIMIT_MAX=100
CORS_ORIGIN=https://your-domain.com
LOG_LEVEL=info
EOF

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api npm run migrate

# Seed initial admin user
docker-compose exec api npm run seed:admin

# Check service health
curl http://localhost:3000/health
```

### Docker Compose Configuration

```yaml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/gated_communities
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
      - JWT_EXPIRY=24h
      - BCRYPT_ROUNDS=12
      - RATE_LIMIT_WINDOW=900000
      - RATE_LIMIT_MAX=100
      - CORS_ORIGIN=${CORS_ORIGIN}
      - LOG_LEVEL=info
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.5"
        reservations:
          memory: 256M
          cpus: "0.25"

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=gated_communities
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./docker/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Production Docker Build

```dockerfile
# docker/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force
COPY . .
RUN npm run build

FROM node:20-alpine AS runner

RUN addgroup -g 1001 -S nodejs && adduser -S gated -u 1001
WORKDIR /app

COPY --from=builder --chown=gated:nodejs /app/dist ./dist
COPY --from=builder --chown=gated:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=gated:nodejs /app/package.json ./

USER gated
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s \
  CMD curl -f http://localhost:3000/health || exit 1

CMD ["node", "dist/app.js"]
```

---

## Kubernetes Deployment

### Namespace and Secrets

```bash
# Create namespace
kubectl create namespace gated-communities

# Create secrets
kubectl create secret generic app-secrets \
  --from-literal=JWT_SECRET="$(openssl rand -base64 32)" \
  --from-literal=DATABASE_URL="postgresql://..." \
  --from-literal=REDIS_URL="redis://..." \
  -n gated-communities
```

### Deployment Manifest

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gated-communities-api
  namespace: gated-communities
  labels:
    app: gated-communities
    component: api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: gated-communities
      component: api
  template:
    metadata:
      labels:
        app: gated-communities
        component: api
    spec:
      containers:
        - name: api
          image: your-registry/gated-communities:latest
          ports:
            - containerPort: 3000
              protocol: TCP
          env:
            - name: PORT
              value: "3000"
            - name: LOG_LEVEL
              value: "info"
            - name: JWT_EXPIRY
              value: "24h"
            - name: BCRYPT_ROUNDS
              value: "12"
            - name: RATE_LIMIT_WINDOW
              value: "900000"
            - name: RATE_LIMIT_MAX
              value: "100"
          envFrom:
            - secretRef:
                name: app-secrets
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          securityContext:
            runAsNonRoot: true
            runAsUser: 1001
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
---
apiVersion: v1
kind: Service
metadata:
  name: gated-communities-api
  namespace: gated-communities
spec:
  selector:
    app: gated-communities
    component: api
  ports:
    - port: 80
      targetPort: 3000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: gated-communities-ingress
  namespace: gated-communities
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
    - hosts:
        - api.your-domain.com
      secretName: gated-communities-tls
  rules:
    - host: api.your-domain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: gated-communities-api
                port:
                  number: 80
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gated-communities-hpa
  namespace: gated-communities
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gated-communities-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n gated-communities
kubectl get svc -n gated-communities
kubectl get ingress -n gated-communities

# Check logs
kubectl logs -f deployment/gated-communities-api -n gated-communities

# Port forward for local testing
kubectl port-forward svc/gated-communities-api 8080:80 -n gated-communities
```

---

## Terraform Deployment

### AWS EKS with RDS

```hcl
# terraform/main.tf
terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket = "gated-communities-tfstate"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

variable "cluster_name" {
  default = "gated-communities-prod"
}

variable "db_password" {
  sensitive = true
}

# VPC and Networking
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Environment = "production"
    Project     = "gated-communities"
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.28"

  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_subnets
  control_plane_subnet_ids       = module.vpc.private_subnets

  cluster_endpoint_private_access = true
  cluster_endpoint_public_access  = true

  eks_managed_node_groups = {
    general = {
      desired_size = 3
      min_size     = 2
      max_size     = 10

      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"

      labels = {
        role = "general"
      }

      update_config = {
        max_unavailable_percentage = 25
      }
    }
  }

  tags = {
    Environment = "production"
    Project     = "gated-communities"
  }
}

# RDS PostgreSQL
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${var.cluster_name}-db"

  engine               = "postgres"
  engine_version       = "15.4"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = "db.t3.medium"

  allocated_storage     = 100
  max_allocated_storage = 500

  db_name  = "gated_communities"
  username = "postgres"
  port     = 5432

  multi_az               = true
  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [aws_security_group.rds.id]

  maintenance_window      = "Mon:00:00-Mon:03:00"
  backup_window           = "03:00-06:00"
  backup_retention_period = 30

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  deletion_protection = true
  storage_encrypted   = true

  tags = {
    Environment = "production"
    Project     = "gated-communities"
  }
}

# ElastiCache Redis
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id = "${var.cluster_name}-redis"
  description          = "Redis cluster for gated-communities"

  node_type            = "cache.t3.medium"
  num_cache_clusters   = 2
  automatic_failover_enabled = true
  multi_az_enabled     = true

  engine_version       = "7.0"
  port                 = 6379
  parameter_group_name = "default.redis7"

  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  snapshot_retention_limit = 7
  snapshot_window         = "05:00-09:00"

  tags = {
    Environment = "production"
    Project     = "gated-communities"
  }
}

# Security Groups
resource "aws_security_group" "rds" {
  name_prefix = "${var.cluster_name}-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }

  tags = {
    Name = "${var.cluster_name}-rds"
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "${var.cluster_name}-redis-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }

  tags = {
    Name = "${var.cluster_name}-redis"
  }
}

# Outputs
output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  value = module.rds.db_instance_endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}
```

### Apply Terraform

```bash
# Initialize Terraform
cd terraform/
terraform init

# Plan changes
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan

# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name gated-communities-prod

# Verify cluster
kubectl get nodes
```

---

## Environment Configuration

### Production Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `PORT` | API server port | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `JWT_SECRET` | Secret for JWT signing (min 32 chars) | Yes |
| `JWT_EXPIRY` | Token expiry duration | Yes |
| `BCRYPT_ROUNDS` | Password hashing rounds (10-14) | Yes |
| `RATE_LIMIT_WINDOW` | Rate limit window in ms | Yes |
| `RATE_LIMIT_MAX` | Max requests per window | Yes |
| `CORS_ORIGIN` | Allowed CORS origins | Yes |
| `LOG_LEVEL` | Logging level | Yes |
| `SENTRY_DSN` | Sentry error tracking DSN | No |
| `SMTP_HOST` | Email server host | No |
| `SMTP_PORT` | Email server port | No |
| `SMTP_USER` | Email server username | No |
| `SMTP_PASS` | Email server password | No |

---

## Database Migrations

### Running Migrations

```bash
# Local development
npm run migrate

# Docker
docker-compose exec api npm run migrate

# Kubernetes
kubectl exec -it deployment/gated-communities-api -n gated-communities -- npm run migrate

# Production (zero-downtime)
# Run migrations as a Kubernetes Job
kubectl apply -f k8s/migration-job.yaml
kubectl wait --for=condition=complete job/db-migrate -n gated-communities --timeout=300s
```

### Migration Best Practices

1. Always backup before running migrations in production
2. Test migrations on a staging environment first
3. Use expand-migrate-contract pattern for zero-downtime deployments
4. Keep migrations idempotent when possible
5. Monitor migration duration and rollback if needed

---

## Health Checks

### Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness probe |
| `GET /health/ready` | Readiness probe |
| `GET /health/deep` | Deep health check (DB, Redis) |

### Example Responses

**Liveness (200):**
```json
{ "status": "ok" }
```

**Readiness (200):**
```json
{
  "status": "ready",
  "checks": {
    "database": "up",
    "redis": "up"
  }
}
```

**Deep Health (200):**
```json
{
  "status": "healthy",
  "version": "1.2.3",
  "uptime": 86400,
  "checks": {
    "database": { "status": "up", "latency_ms": 12 },
    "redis": { "status": "up", "latency_ms": 3 },
    "disk": { "status": "up", "free_gb": 45 }
  }
}
```

---

## Monitoring

### Prometheus Metrics

The application exposes Prometheus metrics at `/metrics`:

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",route="/api/v1/residents",status="200"} 1523

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1",method="GET",route="/api/v1/residents"} 1200

# HELP db_connections_active Active database connections
# TYPE db_connections_active gauge
db_connections_active 12
```

### Grafana Dashboard

Import the provided dashboard from `monitoring/grafana-dashboard.json` for:
- Request rate and error rate
- Response time percentiles
- Database connection pool
- Redis memory usage
- JVM/Node.js memory and CPU

### Alerting Rules

```yaml
# monitoring/alerts.yaml
groups:
  - name: gated-communities
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency above 1 second"

      - alert: DatabaseConnectionsHigh
        expr: db_connections_active > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connections above 80%"
```

---

## Backup and Recovery

### Database Backups

```bash
# Automated daily backups via RDS (AWS) or pg_dump
# Manual backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql $DATABASE_URL < backup_20240115_120000.sql
```

### Redis Backups

```bash
# Redis persistence is enabled (AOF + RDB)
# Manual backup
redis-cli -u $REDIS_URL BGSAVE
# Copy dump.rdb to safe storage
```

### Disaster Recovery

1. **RPO (Recovery Point Objective):** 24 hours (daily backups)
2. **RTO (Recovery Time Objective):** 4 hours
3. **Multi-AZ deployment** for automatic failover
4. **Cross-region backups** for critical data

---

## Troubleshooting

### Common Issues

**Database connection errors:**
```bash
# Check database connectivity
kubectl exec -it deployment/gated-communities-api -n gated-communities -- \
  nc -zv your-rds-endpoint 5432

# Check connection pool settings
kubectl logs deployment/gated-communities-api -n gated-communities | grep -i "pool"
```

**High memory usage:**
```bash
# Check memory usage
kubectl top pods -n gated-communities

# Check for memory leaks
kubectl logs deployment/gated-communities-api -n gated-communities | grep -i "memory"
```

**Pod crash looping:**
```bash
# Check pod status
kubectl describe pod <pod-name> -n gated-communities

# Check previous logs
kubectl logs <pod-name> -n gated-communities --previous
```

### Log Aggregation

```bash
# View logs across all pods
kubectl logs -l app=gated-communities -n gated-communities --tail=100 -f

# Search for errors
kubectl logs -l app=gated-communities -n gated-communities | grep -i error
```

### Getting Help

- Check the [GitHub Issues](https://github.com/your-org/gated-communities/issues)
- Review application logs with `LOG_LEVEL=debug`
- Contact support at support@your-domain.com
