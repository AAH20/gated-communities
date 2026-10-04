"""Bulk operations endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Member, MemberRole
from ..schemas import BulkMemberUpdate
from ..security import require_auth

router = APIRouter()


def _is_admin_or_owner(
    user_id: str | int,
    db: Session,
) -> bool:
    """Check if user is an admin or owner in any community."""
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        return False
    memberships = db.query(Member).filter(Member.user_id == user_id_int).all()
    return any(m.role in (MemberRole.OWNER, MemberRole.ADMIN) for m in memberships)


@router.post("/members/update")
def bulk_update_members(
    update: BulkMemberUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # RBAC: Only admins and owners can perform bulk operations
    if not _is_admin_or_owner(current_user["id"], db):
        raise HTTPException(status_code=403, detail="Forbidden")

    success_count = 0
    failures = []

    for member_id in update.member_ids:
        member = db.query(Member).filter(Member.id == member_id).first()
        if not member:
            failures.append({"id": member_id, "error": "Not found"})
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
