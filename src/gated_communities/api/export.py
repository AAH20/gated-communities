"""Data export endpoints."""

import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Community, Member

router = APIRouter()


@router.get("/members")
def export_members(
    format: str = Query("json", pattern="^(csv|json)$"),
    db: Session = Depends(get_db),
):
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
def export_analytics(db: Session = Depends(get_db)):
    total_communities = db.query(Community).count()
    total_members = db.query(Member).count()
    return {
        "total_communities": total_communities,
        "total_members": total_members,
    }
