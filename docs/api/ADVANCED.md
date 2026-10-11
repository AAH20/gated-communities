# Gated Communities — Advanced API Usage

The official SDK is **Python** (`pip install gated-communities-sdk`), built on
Pydantic v2 with full type hints. This document shows common advanced patterns.

## Install

```bash
pip install gated-communities-sdk
```

## Client

```python
from gated_communities_sdk import GatedCommunitiesClient

with GatedCommunitiesClient(base_url="http://localhost:8000", api_key="...") as client:
    # Resource namespaces: communities, members, users, api_keys, ...
    communities = client.communities.list()
    tiers = client.tiers.list()
```

## Authentication

Obtain a token from the auth endpoint (mounted at the app **root**):

```bash
curl -X POST http://localhost:8000/auth/login   -H "Content-Type: application/json"   -d '{"username": "you", "password": "..."}'
```

Then send it on subsequent requests:

```http
Authorization: Bearer <token>
```

## Error handling

The SDK raises granular exceptions (authentication, authorization, validation,
rate limit, server error) and retries automatically with exponential backoff on
`429` and `5xx`.

```python
from gated_communities_sdk.exceptions import RateLimitError

try:
    client.members.create(name="Ada")
except RateLimitError:
    ...
```

## Webhooks

Register a webhook (root path):

```bash
curl -X POST http://localhost:8000/webhooks   -H "Content-Type: application/json"   -d '{"url": "https://example.com/hooks/gc", "events": ["member.created"]}'
```

Verify inbound webhook signatures before trusting the payload.

## Health & readiness

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
curl http://localhost:8000/live
```
