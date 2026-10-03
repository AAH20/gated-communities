"""Database integration tests."""

import pytest
from sqlalchemy import text
from gated_communities.database import engine, SessionLocal
from gated_communities.models import Community, Member, ModerationItem, AuditLog
from gated_communities.database import Base


class TestDatabaseSchema:
    def test_all_tables_created(self):
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = {row[0] for row in result}
        assert "communities" in tables
        assert "members" in tables
        assert "moderation_items" in tables
        assert "audit_logs" in tables

    def test_community_table_columns(self):
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(communities)"))
            columns = {row[1] for row in result}
        assert "id" in columns
        assert "name" in columns
        assert "description" in columns
        assert "is_private" in columns
        assert "tier_id" in columns
        assert "capacity" in columns

    def test_member_table_columns(self):
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(members)"))
            columns = {row[1] for row in result}
        assert "id" in columns
        assert "email" in columns
        assert "name" in columns
        assert "role" in columns
        assert "community_id" in columns
        assert "is_active" in columns


class TestDatabaseCRUD:
    def test_create_and_query_community(self, db_session):
        community = Community(name="Test", description="Desc", tier_id="free", capacity=50)
        db_session.add(community)
        db_session.commit()
        db_session.refresh(community)
        assert community.id is not None
        result = db_session.query(Community).filter_by(name="Test").first()
        assert result is not None
        assert result.capacity == 50

    def test_create_and_query_member(self, db_session):
        community = Community(name="Test")
        db_session.add(community)
        db_session.commit()
        member = Member(email="test@example.com", name="Test", community_id=community.id)
        db_session.add(member)
        db_session.commit()
        db_session.refresh(member)
        assert member.id is not None
        result = db_session.query(Member).filter_by(email="test@example.com").first()
        assert result is not None

    def test_cascade_delete_community(self, db_session):
        community = Community(name="Test")
        db_session.add(community)
        db_session.commit()
        member = Member(email="test@example.com", name="Test", community_id=community.id)
        db_session.add(member)
        db_session.commit()
        community_id = community.id
        db_session.delete(community)
        db_session.commit()
        result = db_session.query(Member).filter_by(community_id=community_id).first()
        assert result is None

    def test_moderation_item_crud(self, db_session):
        item = ModerationItem(type="spam", author="user1", reason="Spam")
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        assert item.id is not None
        assert item.status == "pending"

    def test_audit_log_crud(self, db_session):
        log = AuditLog(user_id="u1", action="login", resource_type="session")
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)
        assert log.id is not None
        assert log.action == "login"

    def test_update_community(self, db_session):
        community = Community(name="Old Name")
        db_session.add(community)
        db_session.commit()
        community.name = "New Name"
        db_session.commit()
        result = db_session.query(Community).filter_by(id=community.id).first()
        assert result.name == "New Name"

    def test_update_member_role(self, db_session):
        community = Community(name="Test")
        db_session.add(community)
        db_session.commit()
        member = Member(email="test@example.com", name="Test", community_id=community.id, role="member")
        db_session.add(member)
        db_session.commit()
        member.role = "admin"
        db_session.commit()
        result = db_session.query(Member).filter_by(id=member.id).first()
        assert result.role == "admin"


class TestDatabaseRelationships:
    def test_community_member_relationship(self, db_session):
        community = Community(name="Test")
        db_session.add(community)
        db_session.commit()
        m1 = Member(email="a@example.com", name="A", community_id=community.id)
        m2 = Member(email="b@example.com", name="B", community_id=community.id)
        db_session.add_all([m1, m2])
        db_session.commit()
        db_session.refresh(community)
        assert len(community.members) == 2

    def test_member_community_backref(self, db_session):
        community = Community(name="Test")
        db_session.add(community)
        db_session.commit()
        member = Member(email="test@example.com", name="Test", community_id=community.id)
        db_session.add(member)
        db_session.commit()
        db_session.refresh(member)
        assert member.community.name == "Test"


class TestDatabaseConstraints:
    def test_community_name_not_null(self, db_session):
        community = Community(name=None)
        db_session.add(community)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_member_email_not_null(self, db_session):
        community = Community(name="Test")
        db_session.add(community)
        db_session.commit()
        member = Member(email=None, name="Test", community_id=community.id)
        db_session.add(member)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_member_community_fk(self, db_session):
        member = Member(email="test@example.com", name="Test", community_id=9999)
        db_session.add(member)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()
