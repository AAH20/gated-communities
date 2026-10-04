"""Member management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Community, Member, MemberRole
from ..schemas import MemberCreate, MemberResponse
from ..security import require_auth
from ..security.sanitization import sanitize_dict

router = APIRouter()


def _get_user_role(
    user_id: str | int,
    community_id: int,
    db: Session,
) -> MemberRole | None:
    """Get the user's role in a community, or None if not a member."""
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        return None
    membership = (
        db.query(Member)
        .filter(
            Member.community_id == community_id,
            Member.user_id == user_id_int,
        )
        .first()
    )
    return membership.role if membership else None


@router.get("", response_model=list[MemberResponse])
def list_members(
    community_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    query = db.query(Member)
    if community_id:
        query = query.filter(Member.community_id == community_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=MemberResponse, status_code=201)
def create_member(
    member: MemberCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    community = db.query(Community).filter(Community.id == member.community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="Not found")

    # RBAC: Only admins and owners can add members
    user_role = _get_user_role(current_user["id"], member.community_id, db)
    if user_role not in (MemberRole.OWNER, MemberRole.ADMIN):
        raise HTTPException(status_code=403, detail="Forbidden")

    safe_data = sanitize_dict(member.model_dump())
    db_member = Member(**safe_data)
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Not found")
    return member


@router.delete("/{member_id}", status_code=204)
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Not found")

    # RBAC: Only admins and owners can remove members
    user_role = _get_user_role(current_user["id"], member.community_id, db)
    if user_role not in (MemberRole.OWNER, MemberRole.ADMIN):
        raise HTTPException(status_code=403, detail="Forbidden")

    db.delete(member)
    db.commit()
