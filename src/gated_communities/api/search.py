"""Search endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Community, Member
from ..schemas import CommunityResponse, MemberResponse

router = APIRouter()


@router.get("")
def search(
    q: str = Query(..., min_length=1),
    type: str = Query("all", pattern="^(all|communities|members)$"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    results = {"communities": [], "members": []}
    search_pattern = f"%{q}%"

    if type in ("all", "communities"):
        communities = (
            db.query(Community)
            .filter(Community.name.ilike(search_pattern))
            .limit(limit)
            .all()
        )
        results["communities"] = [CommunityResponse.model_validate(c) for c in communities]

    if type in ("all", "members"):
        members = (
            db.query(Member)
            .filter(Member.name.ilike(search_pattern))
            .limit(limit)
            .all()
        )
        results["members"] = [MemberResponse.model_validate(m) for m in members]

    return results
