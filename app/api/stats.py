"""Сводка по базе: сколько вакансий в каком статусе и сколько откликов."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud
from ..db import get_db
from ..schemas import Stats

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=Stats)
def get_stats(db: Session = Depends(get_db)) -> Stats:
    return Stats(**crud.get_stats(db))
