"""Data export endpoints."""

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Community, Member, MemberRole
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


@router.get("/members")
def export_members(
    format: str = Query("json", pattern="^(csv|json)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # RBAC: Only admins and owners can export data
    if not _is_admin_or_owner(current_user["id"], db):
        raise HTTPException(status_code=403, detail="Forbidden")

    members = db.query(Member).all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "email", "name", "role", "community_id", "is_active"])
        for m in members:
            writer.writerow([m.id, m.email, m.name, m.role, m.community_id, m.is_active])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=members.csv"},
        )
    else:
        return JSONResponse(
            content={
                "count": len(members),
                "members": [
                    {
                        "id": m.id,
                        "email": m.email,
                        "name": m.name,
                        "role": m.role,
                        "community_id": m.community_id,
                        "is_active": m.is_active,
                    }
                    for m in members
                ],
            }
        )


@router.get("/analytics")
def export_analytics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # RBAC: Only admins and owners can export analytics
    if not _is_admin_or_owner(current_user["id"], db):
        raise HTTPException(status_code=403, detail="Forbidden")

    total_communities = db.query(Community).count()
    total_members = db.query(Member).count()
    return {
        "total_communities": total_communities,
        "total_members": total_members,
    }
