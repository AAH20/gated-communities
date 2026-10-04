"""Audit log endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import AuditLog, Member, MemberRole
from ..schemas import AuditLogCreate, AuditLogResponse
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


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    user_id: str | None = None,
    resource_type: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # RBAC: Only admins and owners can view audit logs
    if not _is_admin_or_owner(current_user["id"], db):
        raise HTTPException(status_code=403, detail="Forbidden")

    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=AuditLogResponse, status_code=201)
def create_audit_log(
    log: AuditLogCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # RBAC: Only admins and owners can create audit logs
    if not _is_admin_or_owner(current_user["id"], db):
        raise HTTPException(status_code=403, detail="Forbidden")

    db_log = AuditLog(**log.model_dump())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


@router.get("/{log_id}", response_model=AuditLogResponse)
def get_audit_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # RBAC: Only admins and owners can view audit logs
    if not _is_admin_or_owner(current_user["id"], db):
        raise HTTPException(status_code=403, detail="Forbidden")

    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Not found")
    return log
