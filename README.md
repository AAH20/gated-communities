# Gated Communities

> **Unified Gated Community Management Platform**
>
> A production-grade, modular gated community management platform consolidating 10 independent services into a single standalone application with 57 AI-powered agents for tier management, moderation, access control, and governance.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF.svg)](https://github.com/features/actions)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The Gated Communities platform unifies the entire community management lifecycle — from member verification and tier management to moderation, governance, and compliance — into a single, cohesive system. Each domain is powered by specialized AI agents, enabling intelligent automation at every stage of community operations.

### Key Capabilities

| Domain | Capability | Agents |
|--------|-----------|--------|
| Tier Management | Member tier evaluation, benefits, upgrades | 6 |
| Moderation Queue | Auto-moderation, queue optimization, escalation | 7 |
| Access Control | Permission evaluation, role management, policy enforcement | 6 |
| Community Health | Toxicity detection, engagement metrics | 2 |
| Member Verification | Identity verification, fraud prevention, trust scoring | 6 |
| Escalation Workflow | Auto-resolution, SLA tracking, priority routing | 6 |
| Reputation System | Reputation scoring, badges, trust tiers | 6 |
| Compliance Monitor | Policy tracking, violation detection, audits | 6 |
| Moderation Analytics | Trend analysis, predictor, performance metrics | 6 |
| Community Governance | Dispute resolution, rule enforcement, policy management | 6 |

**Total: 57 agents across 10 modules**

---

## Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Web[Web Dashboard]
        Mobile[Mobile App]
        API[External API Clients]
    end

    subgraph "API Gateway"
        GW[FastAPI Router]
        Auth[Authentication]
        RateLimit[Rate Limiting]
    end

    subgraph "Agent Orchestration Layer"
        subgraph "Tier Management"
            TM1[TierEvaluatorAgent]
            TM2[BenefitsManagerAgent]
            TM3[UpgradeProcessorAgent]
            TM4[TierAnalyticsAgent]
            TM5[RetentionAgent]
            TM6[WinBackAgent]
        end
        subgraph "Moderation Queue"
            MQ1[AutoModeratorAgent]
            MQ2[QueueOptimizerAgent]
            MQ3[EscalationRouterAgent]
            MQ4[ContentClassifierAgent]
            MQ5[ActionRecommenderAgent]
            MQ6[HumanReviewAgent]
            MQ7[PatternDetectorAgent]
        end
        subgraph "Access Control"
            AC1[PermissionEvaluatorAgent]
            AC2[RoleManagerAgent]
            AC3[PolicyEnforcerAgent]
            AC4[ResourceGuardAgent]
            AC5[SessionManagerAgent]
            AC6[AuditLoggerAgent]
        end
        subgraph "Community Health"
            CH1[ToxicityDetectorAgent]
            CH2[EngagementMetricsAgent]
        end
        subgraph "Member Verification"
            MV1[IdentityVerifierAgent]
            MV2[FraudPreventerAgent]
            MV3[TrustScorerAgent]
            MV4[KYCProcessorAgent]
            MV5[DocumentVerifierAgent]
            MV6[BiometricCheckerAgent]
        end
        subgraph "Escalation Workflow"
            EW1[AutoResolverAgent]
            EW2[SLATrackerAgent]
            EW3[PriorityRouterAgent]
            EW4[NotificationAgent]
            EW5[ResolutionTrackerAgent]
            EW6[FeedbackCollectorAgent]
        end
        subgraph "Reputation System"
            RS1[ReputationScorerAgent]
            RS2[BadgeManagerAgent]
            RS3[TrustTierAgent]
            RS4[RewardDistributorAgent]
            RS5[PenaltyEnforcerAgent]
            RS6[HistoryTrackerAgent]
        end
        subgraph "Compliance Monitor"
            CO1[PolicyTrackerAgent]
            CO2[ViolationDetectorAgent]
            CO3[AuditManagerAgent]
            CO4[ReportGeneratorAgent]
            CO5[AlertManagerAgent]
            CO6[RemediationAgent]
        end
        subgraph "Moderation Analytics"
            MA1[TrendAnalyzerAgent]
            MA2[PredictorAgent]
            MA3[PerformanceMetricsAgent]
            MA4[ReportGeneratorAgent]
            MA5[DashboardAgent]
            MA6[AlertAgent]
        end
        subgraph "Community Governance"
            CG1[DisputeResolverAgent]
            CG2[RuleEnforcerAgent]
            CG3[PolicyManagerAgent]
            CG4[VotingSystemAgent]
            CG5[AnnouncementAgent]
            CG6[FeedbackProcessorAgent]
        end
    end

    subgraph "Service Layer"
        SV1[Tier Service]
        SV2[Moderation Service]
        SV3[Access Control Service]
        SV4[Verification Service]
        SV5[Governance Service]
    end

    subgraph "Integration Layer"
        INT1[LLM Integration]
        INT2[Database]
        INT3[Cache]
        INT4[Notifications]
    end

    subgraph "Config Layer"
        CF1[Settings]
        CF2[Logging]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL)]
        CACHE[(Redis)]
    end

    Web --> GW
    Mobile --> GW
    API --> GW
    GW --> Auth --> RateLimit

    RateLimit --> TM1 & TM2 & TM3 & TM4 & TM5 & TM6
    RateLimit --> MQ1 & MQ2 & MQ3 & MQ4 & MQ5 & MQ6 & MQ7
    RateLimit --> AC1 & AC2 & AC3 & AC4 & AC5 & AC6
    RateLimit --> CH1 & CH2
    RateLimit --> MV1 & MV2 & MV3 & MV4 & MV5 & MV6
    RateLimit --> EW1 & EW2 & EW3 & EW4 & EW5 & EW6
    RateLimit --> RS1 & RS2 & RS3 & RS4 & RS5 & RS6
    RateLimit --> CO1 & CO2 & CO3 & CO4 & CO5 & CO6
    RateLimit --> MA1 & MA2 & MA3 & MA4 & MA5 & MA6
    RateLimit --> CG1 & CG2 & CG3 & CG4 & CG5 & CG6

    TM1 & TM2 & TM3 & TM4 & TM5 & TM6 --> SV1
    MQ1 & MQ2 & MQ3 & MQ4 & MQ5 & MQ6 & MQ7 --> SV2
    AC1 & AC2 & AC3 & AC4 & AC5 & AC6 --> SV3
    MV1 & MV2 & MV3 & MV4 & MV5 & MV6 --> SV4
    CG1 & CG2 & CG3 & CG4 & CG5 & CG6 --> SV5

    SV1 & SV2 & SV3 & SV4 & SV5 --> INT1 & INT2 & INT3 & INT4
    SV1 & SV2 & SV3 & SV4 & SV5 --> CF1 & CF2
    INT1 & INT2 & INT3 & INT4 --> DB & CACHE
```

### Project Structure

```
gated-communities/
├── src/gated_communities/
│   ├── agents/                    # 57 AI agents across 10 modules
│   │   ├── tier_management/        # Tier management agents
│   │   ├── moderation_queue/       # Moderation queue agents
│   │   ├── access_control/         # Access control agents
│   │   ├── community_health_scorer/# Community health agents
│   │   ├── member_verification/    # Member verification agents
│   │   ├── escalation_workflow/    # Escalation workflow agents
│   │   ├── reputation_system/      # Reputation system agents
│   │   ├── compliance_monitor/     # Compliance monitor agents
│   │   ├── moderation_analytics/   # Moderation analytics agents
│   │   └── community_governance/   # Community governance agents
│   ├── api/
│   │   ├── routes/                # API endpoint handlers
│   │   ├── router.py              # API router configuration
│   │   └── dependencies.py        # Shared dependencies
│   ├── config/                    # Configuration management
│   ├── integrations/              # External service clients
│   ├── models/                    # Pydantic schemas
│   ├── services/                  # Business logic layer
│   └── tests/                     # Test suite
├── k8s/                           # Kubernetes manifests
├── docs/                          # Documentation
├── monitoring/                    # Monitoring configuration
├── .github/workflows/             # CI/CD pipelines
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## Features

- **57 AI-Powered Agents** — Specialized agents for every community management domain
- **Tier Management** — Automated tier evaluation, benefits, and upgrades
- **Moderation Queue** — Auto-moderation with human review escalation
- **Access Control** — Fine-grained permission evaluation and policy enforcement
- **Member Verification** — Identity verification, KYC, and fraud prevention
- **Reputation System** — Reputation scoring, badges, and trust tiers
- **Compliance Monitor** — Policy tracking, violation detection, and audits
- **Escalation Workflow** — Auto-resolution with SLA tracking
- **Community Governance** — Dispute resolution, voting, and rule enforcement
- **RESTful API** — Full OpenAPI documentation
- **Production-Ready** — Docker, Kubernetes, monitoring, and CI/CD included

---

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional)
- Kubernetes cluster (for production)

### Local Development

```bash
# Clone the repository
git clone https://github.com/AAH20/gated-communities.git
cd gated-communities

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
uvicorn gated_communities.main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker Compose (Recommended)

```bash
docker-compose up -d
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

---

## API Reference

All endpoints are prefixed with `/api/v1`:

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/ready` | Readiness probe |
| GET | `/metrics` | Prometheus metrics |

### Tier Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/tiers/evaluate` | Evaluate member tier |
| GET | `/api/v1/tiers/benefits/:tier_id` | Get tier benefits |
| POST | `/api/v1/tiers/upgrade` | Process tier upgrade |
| GET | `/api/v1/tiers/analytics` | Get tier analytics |
| POST | `/api/v1/tiers/retention` | Run retention analysis |
| POST | `/api/v1/tiers/win-back` | Execute win-back campaign |

### Moderation Queue

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/moderation/auto` | Auto-moderate content |
| GET | `/api/v1/moderation/queue` | Get moderation queue |
| POST | `/api/v1/moderation/escalate` | Escalate to human review |
| POST | `/api/v1/moderation/classify` | Classify content |
| POST | `/api/v1/moderation/action` | Recommend action |
| POST | `/api/v1/moderation/human-review` | Submit for human review |
| GET | `/api/v1/moderation/patterns` | Get detected patterns |

### Access Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/access/evaluate` | Evaluate permissions |
| POST | `/api/v1/access/role` | Manage roles |
| POST | `/api/v1/access/policy` | Enforce policy |
| GET | `/api/v1/access/resource/:resource_id` | Guard resource |
| POST | `/api/v1/access/session` | Manage session |
| GET | `/api/v1/access/audit` | Get audit log |

### Community Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/health/toxicity` | Detect toxicity |
| GET | `/api/v1/health/engagement` | Get engagement metrics |

### Member Verification

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/verification/identity` | Verify identity |
| POST | `/api/v1/verification/fraud-check` | Check for fraud |
| GET | `/api/v1/verification/trust/:user_id` | Get trust score |
| POST | `/api/v1/verification/kyc` | Process KYC |
| POST | `/api/v1/verification/document` | Verify document |
| POST | `/api/v1/verification/biometric` | Biometric check |

### Escalation Workflow

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/escalation/auto-resolve` | Auto-resolve issue |
| GET | `/api/v1/escalation/sla/:ticket_id` | Track SLA |
| POST | `/api/v1/escalation/route` | Route by priority |
| POST | `/api/v1/escalation/notify` | Send notification |
| GET | `/api/v1/escalation/resolution/:ticket_id` | Track resolution |
| POST | `/api/v1/escalation/feedback` | Collect feedback |

### Reputation System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/reputation/score/:user_id` | Get reputation score |
| POST | `/api/v1/reputation/badge` | Award badge |
| GET | `/api/v1/reputation/trust-tier/:user_id` | Get trust tier |
| POST | `/api/v1/reputation/reward` | Distribute reward |
| POST | `/api/v1/reputation/penalty` | Enforce penalty |
| GET | `/api/v1/reputation/history/:user_id` | Get history |

### Compliance Monitor

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/compliance/policy` | Track policies |
| POST | `/api/v1/compliance/violation` | Detect violation |
| GET | `/api/v1/compliance/audit` | Get audit report |
| POST | `/api/v1/compliance/report` | Generate report |
| POST | `/api/v1/compliance/alert` | Send alert |
| POST | `/api/v1/compliance/remediation` | Remediate issue |

### Moderation Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/trends` | Get trend analysis |
| GET | `/api/v1/analytics/predict` | Get predictions |
| GET | `/api/v1/analytics/performance` | Get performance metrics |
| GET | `/api/v1/analytics/report` | Get report |
| GET | `/api/v1/analytics/dashboard` | Get dashboard data |
| POST | `/api/v1/analytics/alert` | Send alert |

### Community Governance

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/governance/dispute` | Resolve dispute |
| POST | `/api/v1/governance/rule` | Enforce rule |
| POST | `/api/v1/governance/policy` | Manage policy |
| POST | `/api/v1/governance/vote` | Process vote |
| POST | `/api/v1/governance/announce` | Make announcement |
| POST | `/api/v1/governance/feedback` | Process feedback |

---

## Deployment

### Docker Compose (Development)

```bash
docker-compose up -d
```

### Kubernetes (Production)

```bash
# Apply base manifests
kubectl apply -f k8s/base/

# Apply production overlay
kubectl apply -f k8s/overlays/production/

# Verify deployment
kubectl get pods -n gated-communities
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `REDIS_URL` | — | Redis connection string |
| `LLM_API_KEY` | — | OpenAI API key |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENVIRONMENT` | `production` | Deployment environment |

---

## Configuration

All settings are configurable via environment variables or `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/gated_communities
REDIS_URL=redis://localhost:6379/0
LLM_API_KEY=your-openai-key
LOG_LEVEL=INFO
ENVIRONMENT=production
```

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/gated_communities --cov-report=term-missing

# Run specific test file
pytest src/gated_communities/tests/test_agents.py

# Run with verbose output
pytest -v
```

---

## Monitoring

Prometheus metrics and health checks are available at:

- `/api/v1/health` — Health check
- `/api/v1/ready` — Readiness check
- `/metrics` — Prometheus metrics

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the AGPL-3.0 License — see the [LICENSE](LICENSE) file for details.
