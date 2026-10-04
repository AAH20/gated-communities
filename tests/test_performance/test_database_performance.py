"""Database query performance benchmarks.

Measures query latency, join performance, and bulk operations.
"""

from __future__ import annotations

import time

import pytest

from .conftest import run_benchmark


class TestDatabaseQueryPerformance:
    """Benchmark database query performance."""

    def test_simple_select(self, db_session):
        """Benchmark a simple SELECT 1 query."""
        from sqlalchemy import text

        result = run_benchmark(
            lambda: db_session.execute(text("SELECT 1")), iterations=100
        )
        assert result["avg_ms"] < 10, f"Simple select too slow: {result['avg_ms']}ms"

    def test_count_communities(self, db_session, populated_db):
        """Benchmark counting communities."""
        from sqlalchemy import text

        result = run_benchmark(
            lambda: db_session.execute(text("SELECT COUNT(*) FROM communities")),
            iterations=50,
        )
        assert result["avg_ms"] < 20, f"Count communities too slow: {result['avg_ms']}ms"

    def test_count_members(self, db_session, populated_db):
        """Benchmark counting members."""
        from sqlalchemy import text

        result = run_benchmark(
            lambda: db_session.execute(text("SELECT COUNT(*) FROM members")),
            iterations=50,
        )
        assert result["avg_ms"] < 20, f"Count members too slow: {result['avg_ms']}ms"

    def test_count_moderation_items(self, db_session, populated_db):
        """Benchmark counting moderation items."""
        from sqlalchemy import text

        result = run_benchmark(
            lambda: db_session.execute(text("SELECT COUNT(*) FROM moderation_items")),
            iterations=50,
        )
        assert result["avg_ms"] < 20, f"Count moderation items too slow: {result['avg_ms']}ms"

    def test_count_audit_logs(self, db_session, populated_db):
        """Benchmark counting audit logs."""
        from sqlalchemy import text

        result = run_benchmark(
            lambda: db_session.execute(text("SELECT COUNT(*) FROM audit_logs")),
            iterations=50,
        )
        assert result["avg_ms"] < 20, f"Count audit logs too slow: {result['avg_ms']}ms"

    def test_select_all_communities(self, db_session, populated_db):
        """Benchmark selecting all communities."""
        from gated_communities.models import Community

        result = run_benchmark(
            lambda: db_session.query(Community).all(), iterations=50
        )
        assert result["avg_ms"] < 50, f"Select all communities too slow: {result['avg_ms']}ms"

    def test_select_all_members(self, db_session, populated_db):
        """Benchmark selecting all members."""
        from gated_communities.models import Member

        result = run_benchmark(
            lambda: db_session.query(Member).all(), iterations=50
        )
        assert result["avg_ms"] < 50, f"Select all members too slow: {result['avg_ms']}ms"

    def test_filter_communities_by_tier(self, db_session, populated_db):
        """Benchmark filtering communities by tier."""
        from gated_communities.models import Community, CommunityTier

        result = run_benchmark(
            lambda: db_session.query(Community)
            .filter(Community.tier == CommunityTier.FREE)
            .all(),
            iterations=50,
        )
        assert result["avg_ms"] < 30, f"Filter by tier too slow: {result['avg_ms']}ms"

    def test_filter_communities_by_status(self, db_session, populated_db):
        """Benchmark filtering communities by status."""
        from gated_communities.models import Community

        result = run_benchmark(
            lambda: db_session.query(Community)
            .filter(Community.status == "active")
            .all(),
            iterations=50,
        )
        assert result["avg_ms"] < 30, f"Filter by status too slow: {result['avg_ms']}ms"

    def test_filter_communities_by_tier_enum(self, db_session, populated_db):
        """Benchmark filtering communities by tier using enum."""
        from gated_communities.models import Community, CommunityTier

        result = run_benchmark(
            lambda: db_session.query(Community)
            .filter(Community.tier == CommunityTier.FREE)
            .all(),
            iterations=50,
        )
        assert result["avg_ms"] < 30, f"Filter by tier (enum) too slow: {result['avg_ms']}ms"

    def test_filter_members_by_community(self, db_session, populated_db):
        """Benchmark filtering members by community."""
        from gated_communities.models import Member

        result = run_benchmark(
            lambda: db_session.query(Member)
            .filter(Member.community_id == 1)
            .all(),
            iterations=50,
        )
        assert result["avg_ms"] < 30, f"Filter members by community too slow: {result['avg_ms']}ms"

    def test_filter_members_by_role(self, db_session, populated_db):
        """Benchmark filtering members by role."""
        from gated_communities.models import Member, MemberRole

        result = run_benchmark(
            lambda: db_session.query(Member)
            .filter(Member.role == MemberRole.ADMIN)
            .all(),
            iterations=50,
        )
        assert result["avg_ms"] < 30, f"Filter members by role too slow: {result['avg_ms']}ms"

    def test_join_communities_members(self, db_session, populated_db):
        """Benchmark joining communities and members."""
        from gated_communities.models import Community, Member

        def join_query():
            return (
                db_session.query(Community, Member)
                .join(Member, Community.id == Member.community_id)
                .limit(100)
                .all()
            )

        result = run_benchmark(join_query, iterations=30)
        assert result["avg_ms"] < 100, f"Join query too slow: {result['avg_ms']}ms"

    def test_left_join_communities_members(self, db_session, populated_db):
        """Benchmark left joining communities and members."""
        from sqlalchemy import text

        result = run_benchmark(
            lambda: db_session.execute(
                text(
                    "SELECT c.name, COUNT(m.id) FROM communities c "
                    "LEFT JOIN members m ON m.community_id = c.id "
                    "GROUP BY c.name LIMIT 100"
                )
            ),
            iterations=30,
        )
        assert result["avg_ms"] < 100, f"Left join too slow: {result['avg_ms']}ms"

    def test_aggregate_member_count_by_community(self, db_session, populated_db):
        """Benchmark aggregating member counts by community."""
        from sqlalchemy import text

        result = run_benchmark(
            lambda: db_session.execute(
                text(
                    "SELECT community_id, COUNT(*) as member_count "
                    "FROM members GROUP BY community_id"
                )
            ),
            iterations=30,
        )
        assert result["avg_ms"] < 50, f"Aggregate query too slow: {result['avg_ms']}ms"

    def test_order_communities_by_name(self, db_session, populated_db):
        """Benchmark ordering communities by name."""
        from gated_communities.models import Community

        result = run_benchmark(
            lambda: db_session.query(Community)
            .order_by(Community.name)
            .all(),
            iterations=50,
        )
        assert result["avg_ms"] < 50, f"Order by name too slow: {result['avg_ms']}ms"

    def test_paginated_members(self, db_session, populated_db):
        """Benchmark paginated member queries."""
        from gated_communities.models import Member

        result = run_benchmark(
            lambda: db_session.query(Member).offset(50).limit(50).all(),
            iterations=50,
        )
        assert result["avg_ms"] < 30, f"Paginated query too slow: {result['avg_ms']}ms"

    def test_insert_community(self, db_session):
        """Benchmark inserting a community."""
        from gated_communities.models import Community, CommunityTier

        def insert_community():
            c = Community(
                name="Bench Community",
                description="Benchmark",
                tier=CommunityTier.FREE,
                status="ACTIVE",
            )
            db_session.add(c)
            db_session.commit()
            db_session.delete(c)
            db_session.commit()

        result = run_benchmark(insert_community, iterations=30)
        assert result["avg_ms"] < 50, f"Insert community too slow: {result['avg_ms']}ms"

    def test_insert_member(self, db_session, populated_db):
        """Benchmark inserting a member."""
        from gated_communities.models import Member, MemberRole

        def insert_member():
            m = Member(
                community_id=1,
                user_id=9999,
                role=MemberRole.MEMBER,
            )
            db_session.add(m)
            db_session.commit()
            db_session.delete(m)
            db_session.commit()

        result = run_benchmark(insert_member, iterations=30)
        assert result["avg_ms"] < 50, f"Insert member too slow: {result['avg_ms']}ms"

    def test_update_community(self, db_session, populated_db):
        """Benchmark updating a community."""
        from gated_communities.models import Community

        def update_community():
            c = db_session.query(Community).filter(Community.id == 1).first()
            if c:
                c.name = "Updated Name"
                db_session.commit()
                c.name = "Community 0"
                db_session.commit()

        result = run_benchmark(update_community, iterations=30)
        assert result["avg_ms"] < 50, f"Update community too slow: {result['avg_ms']}ms"

    def test_delete_community(self, db_session, populated_db):
        """Benchmark deleting a community."""
        from gated_communities.models import Community, CommunityTier

        def delete_community():
            c = Community(
                name="Delete Me",
                description="To be deleted",
                tier=CommunityTier.FREE,
                status="ACTIVE",
            )
            db_session.add(c)
            db_session.commit()
            db_id = c.id
            db_session.delete(c)
            db_session.commit()

        result = run_benchmark(delete_community, iterations=30)
        assert result["avg_ms"] < 50, f"Delete community too slow: {result['avg_ms']}ms"

    def test_bulk_insert_members(self, db_session, populated_db):
        """Benchmark bulk inserting members."""
        from gated_communities.models import Member

        def bulk_insert():
            members = [
                Member(
                    community_id=1,
                    user_id=f"bulk_{i}",
                    role="member",
                )
                for i in range(50)
            ]
            db_session.bulk_save_objects(members)
            db_session.commit()
            # Clean up
            db_session.query(Member).filter(
                Member.user_id.like("bulk_%")
            ).delete(synchronize_session=False)
            db_session.commit()

        result = run_benchmark(bulk_insert, iterations=10)
        assert result["avg_ms"] < 200, f"Bulk insert too slow: {result['avg_ms']}ms"

    def test_subquery_member_count(self, db_session, populated_db):
        """Benchmark subquery for member counts."""
        from sqlalchemy import text

        result = run_benchmark(
            lambda: db_session.execute(
                text(
                    "SELECT c.name, "
                    "(SELECT COUNT(*) FROM members m WHERE m.community_id = c.id) as cnt "
                    "FROM communities c LIMIT 50"
                )
            ),
            iterations=30,
        )
        assert result["avg_ms"] < 100, f"Subquery too slow: {result['avg_ms']}ms"

    def test_complex_filter_query(self, db_session, populated_db):
        """Benchmark complex filter query."""
        from gated_communities.models import Community, CommunityTier

        def complex_query():
            return (
                db_session.query(Community)
                .filter(Community.status == "active")
                .filter(Community.tier.in_([CommunityTier.FREE, CommunityTier.BASIC]))
                .order_by(Community.name)
                .limit(20)
                .all()
            )

        result = run_benchmark(complex_query, iterations=30)
        assert result["avg_ms"] < 50, f"Complex filter too slow: {result['avg_ms']}ms"

    def test_text_search_on_communities(self, db_session, populated_db):
        """Benchmark text search on community names."""
        from sqlalchemy import text

        result = run_benchmark(
            lambda: db_session.execute(
                text(
                    "SELECT * FROM communities WHERE name LIKE '%Community%' LIMIT 20"
                )
            ),
            iterations=30,
        )
        assert result["avg_ms"] < 50, f"Text search too slow: {result['avg_ms']}ms"

    def test_date_range_query(self, db_session, populated_db):
        """Benchmark date range query on audit logs."""
        from sqlalchemy import text

        result = run_benchmark(
            lambda: db_session.execute(
                text(
                    "SELECT * FROM audit_logs "
                    "WHERE created_at > datetime('now', '-30 days') LIMIT 50"
                )
            ),
            iterations=30,
        )
        assert result["avg_ms"] < 50, f"Date range query too slow: {result['avg_ms']}ms"
