# Gated Communities — Performance Benchmark Report

**Date:** 2026-10-04T18:50:59+0300

## Summary

## API Performance

| Benchmark | Avg (ms) | Min (ms) | Max (ms) | P95 (ms) | P99 (ms) |
|-----------|----------|----------|----------|----------|----------|
| api_health | 0.41 | 0.21 | 1.08 | N/A | N/A |
| api_root | 0.4 | 0.2 | 0.78 | N/A | N/A |
| api_ready | 0.23 | 0.2 | 0.4 | N/A | N/A |
| api_live | 0.22 | 0.2 | 0.41 | N/A | N/A |
| api_list_communities | 0.23 | 0.21 | 0.34 | N/A | N/A |
| api_list_members | 0.6 | 0.21 | 18.53 | N/A | N/A |
| api_create_community | 0.25 | 0.22 | 0.44 | N/A | N/A |

## Database Performance

| Benchmark | Avg (ms) | Min (ms) | Max (ms) | P95 (ms) | P99 (ms) |
|-----------|----------|----------|----------|----------|----------|
| db_simple_select | 0.02 | 0.01 | 0.21 | N/A | N/A |
| db_count_communities | 0.02 | 0.01 | 0.09 | N/A | N/A |
| db_count_members | 0.01 | 0.01 | 0.04 | N/A | N/A |
| db_count_moderation | 0.01 | 0.01 | 0.03 | N/A | N/A |
| db_count_audit | 0.01 | 0.01 | 0.04 | N/A | N/A |
| db_join_communities_members | 0.05 | 0.05 | 0.1 | N/A | N/A |
| db_filter_by_tier | 0.02 | 0.02 | 0.04 | N/A | N/A |
| db_filter_by_status | 0.02 | 0.02 | 0.12 | N/A | N/A |
| db_order_by_name | 0.02 | 0.02 | 0.07 | N/A | N/A |
| db_paginated_members | 0.02 | 0.02 | 0.06 | N/A | N/A |
| db_aggregate_member_count | 0.03 | 0.02 | 0.06 | N/A | N/A |
| db_text_search | 0.02 | 0.02 | 0.05 | N/A | N/A |
| db_orm_all_communities | 0.22 | 0.19 | 0.85 | N/A | N/A |
| db_orm_all_members | 0.67 | 0.61 | 1.1 | N/A | N/A |
| db_orm_filter_tier | 0.13 | 0.11 | 0.68 | N/A | N/A |
| db_orm_filter_status | 0.23 | 0.21 | 0.64 | N/A | N/A |
| db_orm_filter_members_community | 0.09 | 0.08 | 0.59 | N/A | N/A |
| db_orm_order_communities | 0.21 | 0.2 | 0.43 | N/A | N/A |
| db_orm_paginated_members | 0.22 | 0.19 | 0.56 | N/A | N/A |

## Concurrent Performance

| Benchmark | Avg (ms) | Min (ms) | Max (ms) | P95 (ms) | P99 (ms) |
|-----------|----------|----------|----------|----------|----------|
| concurrent_health_100 | N/A | N/A | N/A | N/A | N/A |
| concurrent_mixed_50 | N/A | N/A | N/A | N/A | N/A |

## Bottlenecks

No significant bottlenecks identified.

## Recommendations

1. **Database**: Add indexes on frequently queried columns (tier_id, is_private, community_id).
2. **API**: Implement caching for read-heavy endpoints.
3. **Agents**: Cache agent results for repeated inputs.
4. **Concurrent**: Use connection pooling and async database drivers.
