"""Community CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import Community
from ..schemas import CommunityCreate, CommunityResponse
from ..auth import get_current_user

router = APIRouter()


@router.get("", response_model=List[CommunityResponse])
def list_communities(
    include_private: bool = False,
    tier_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = db.query(Community)
    if not include_private:
        query = query.filter(Community.is_private == False)
    if tier_id:
        query = query.filter(Community.tier_id == tier_id)
    return query.all()


@router.post("", response_model=CommunityResponse, status_code=201)
def create_community(
    community: CommunityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_community = Community(**community.model_dump())
    db.add(db_community)
    db.commit()
    db.refresh(db_community)
    return db_community


@router.get("/{community_id}", response_model=CommunityResponse)
def get_community(
    community_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    return community


@router.delete("/{community_id}", status_code=204)
def delete_community(
    community_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    db.delete(community)
    db.commit()
