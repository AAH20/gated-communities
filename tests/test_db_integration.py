"""Database integration tests.

These exercise the SQLAlchemy models in ``gated_communities.models`` (the source
of truth for the schema) against the in-memory SQLite database provided by the
``db_session`` fixture.  Column assertions are derived from the ORM metadata so
they cannot drift from the models the application actually uses.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from gated_communities.models import (
    AuditLog,
    Community,
    CommunityStatus,
    CommunityTier,
    Member,
    MemberRole,
    ModerationItem,
)


def _tables(db_session) -> set[str]:
    rows = db_session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table'")
    ).fetchall()
    return {row[0] for row in rows}


def _columns(db_session, table: str) -> set[str]:
    rows = db_session.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {row[1] for row in rows}


def _make_community(db_session, name: str = "Test Community") -> Community:
    community = Community(name=name)
    db_session.add(community)
    db_session.commit()
    db_session.refresh(community)
    return community


class TestDatabaseSchema:
    def test_all_tables_created(self, db_session):
        tables = _tables(db_session)
        assert {"communities", "members", "moderation_items", "audit_logs"} <= tables

    def test_community_table_columns(self, db_session):
        assert _columns(db_session, "communities") == {
            "id",
            "name",
            "description",
            "tier",
            "status",
            "created_at",
            "updated_at",
        }

    def test_member_table_columns(self, db_session):
        assert _columns(db_session, "members") == {
            "id",
            "community_id",
            "user_id",
            "role",
            "joined_at",
            "updated_at",
        }


class TestDatabaseCRUD:
    def test_create_and_query_community(self, db_session):
        community = Community(
            name="Test Community",
            description="Desc",
            tier=CommunityTier.FREE,
            status=CommunityStatus.ACTIVE,
        )
        db_session.add(community)
        db_session.commit()
        db_session.refresh(community)
        assert community.id is not None
        result = db_session.query(Community).filter_by(name="Test Community").first()
        assert result is not None
        assert result.description == "Desc"

    def test_create_and_query_member(self, db_session):
        community = _make_community(db_session)
        member = Member(
            community_id=community.id,
            user_id=42,
            role=MemberRole.MEMBER,
        )
        db_session.add(member)
        db_session.commit()
        db_session.refresh(member)
        assert member.id is not None
        result = db_session.query(Member).filter_by(user_id=42).first()
        assert result is not None

    def test_cascade_delete_community(self, db_session):
        community = _make_community(db_session)
        member = Member(community_id=community.id, user_id=7)
        db_session.add(member)
        db_session.commit()
        community_id = community.id
        db_session.delete(community)
        db_session.commit()
        result = db_session.query(Member).filter_by(community_id=community_id).first()
        assert result is None

    def test_moderation_item_crud(self, db_session):
        community = _make_community(db_session)
        item = ModerationItem(
            community_id=community.id,
            reporter_id=1,
            target_type="post",
            target_id=5,
            reason="Spam",
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        assert item.id is not None
        assert item.status == "pending"

    def test_audit_log_crud(self, db_session):
        community = _make_community(db_session)
        log = AuditLog(community_id=community.id, user_id=1, action="login")
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)
        assert log.id is not None
        assert log.action == "login"

    def test_update_community(self, db_session):
        community = _make_community(db_session, name="Old Name")
        community.name = "New Name"
        db_session.commit()
        result = db_session.query(Community).filter_by(id=community.id).first()
        assert result.name == "New Name"

    def test_update_member_role(self, db_session):
        community = _make_community(db_session)
        member = Member(
            community_id=community.id,
            user_id=3,
            role=MemberRole.MEMBER,
        )
        db_session.add(member)
        db_session.commit()
        member.role = MemberRole.ADMIN
        db_session.commit()
        result = db_session.query(Member).filter_by(id=member.id).first()
        assert result.role == MemberRole.ADMIN


class TestDatabaseRelationships:
    def test_community_member_relationship(self, db_session):
        community = _make_community(db_session)
        m1 = Member(community_id=community.id, user_id=1)
        m2 = Member(community_id=community.id, user_id=2)
        db_session.add_all([m1, m2])
        db_session.commit()
        db_session.refresh(community)
        assert len(community.members) == 2

    def test_member_community_backref(self, db_session):
        community = _make_community(db_session, name="Backref Community")
        member = Member(community_id=community.id, user_id=9)
        db_session.add(member)
        db_session.commit()
        db_session.refresh(member)
        assert member.community.name == "Backref Community"


class TestDatabaseConstraints:
    def test_community_name_not_null(self, db_session):
        community = Community(name=None)
        db_session.add(community)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_member_user_id_not_null(self, db_session):
        community = _make_community(db_session)
        member = Member(community_id=community.id, user_id=None)
        db_session.add(member)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_member_community_fk(self, db_session):
        member = Member(community_id=9999, user_id=1)
        db_session.add(member)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()
