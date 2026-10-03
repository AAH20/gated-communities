"""Moderation queue endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import ModerationItem
from ..schemas import ModerationItemCreate, ModerationItemResponse

router = APIRouter()


@router.get("/queue", response_model=List[ModerationItemResponse])
def get_moderation_queue(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return db.query(ModerationItem).filter(ModerationItem.status == "pending").offset(skip).limit(limit).all()


@router.post("/items", response_model=ModerationItemResponse, status_code=201)
def create_moderation_item(item: ModerationItemCreate, db: Session = Depends(get_db)):
    db_item = ModerationItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
