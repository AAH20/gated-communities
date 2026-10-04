"""Community CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Community, Member, MemberRole
from ..schemas import CommunityCreate, CommunityResponse
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


@router.get("", response_model=list[CommunityResponse])
def list_communities(
    include_private: bool = False,
    tier_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    query = db.query(Community)
    if tier_id:
        query = query.filter(Community.tier_id == tier_id)
    return query.all()


@router.post("", response_model=CommunityResponse, status_code=201)
def create_community(
    community: CommunityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    safe_data = sanitize_dict(community.model_dump(), html_fields={"description"})
    db_community = Community(**safe_data)
    db.add(db_community)
    db.commit()
    db.refresh(db_community)
    return db_community


@router.get("/{community_id}", response_model=CommunityResponse)
def get_community(
    community_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        # Return generic "Not found" to avoid information disclosure
        raise HTTPException(status_code=404, detail="Not found")
    return community


@router.delete("/{community_id}", status_code=204)
def delete_community(
    community_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="Not found")

    # RBAC: Only owners and admins can delete communities
    user_role = _get_user_role(current_user["id"], community_id, db)
    if user_role not in (MemberRole.OWNER, MemberRole.ADMIN):
        raise HTTPException(status_code=403, detail="Forbidden")

    db.delete(community)
    db.commit()
