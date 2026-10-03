"""Bulk operations endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Member
from ..schemas import BulkMemberUpdate

router = APIRouter()


@router.post("/members/update")
def bulk_update_members(update: BulkMemberUpdate, db: Session = Depends(get_db)):
    success_count = 0
    failures = []

    for member_id in update.member_ids:
        member = db.query(Member).filter(Member.id == member_id).first()
        if not member:
            failures.append({"id": member_id, "error": "Member not found"})
            continue

        if update.action == "remove":
            member.is_active = False
        elif update.action == "add":
            member.is_active = True
        elif update.action == "update" and update.role:
            member.role = update.role

        success_count += 1

    db.commit()
    return {
        "success_count": success_count,
        "failure_count": len(failures),
        "failures": failures,
    }
