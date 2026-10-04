"""Endpoints d'espai"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session


from plataforma_iot.api.dependencies import current_role, require_admin
from plataforma_iot.api.schemas import SpaceIn, SpaceOut
from plataforma_iot.db import get_db
from plataforma_iot.models.space import Space
from plataforma_iot.api.queries.readings import BUCKETS, series, summarize
from plataforma_iot.api.schemas import ReadingBucketOut, ReadingSummaryOut

router = APIRouter(
    prefix="/spaces",
    tags=["spaces"],
    dependencies=[Depends(current_role)],
)

@router.get("", response_model=list[SpaceOut])
def list_spaces(session: Session = Depends(get_db)) -> list[Space]:
    """Torna tots els espais"""

    return list(session.scalars(select(Space).order_by(Space.id)))

@router.get("/{space_id}", response_model=SpaceOut)
def get_space(space_id: int, session: Session = Depends(get_db)) -> Space:
    """Torna un espai donat un id"""

    space = session.get(Space, space_id)
    if space is None:
        raise HTTPException(status_code=404, detail="Espai no trobat")
    return space

@router.post("", response_model=SpaceOut, status_code=201, dependencies=[Depends(require_admin)])
def create_space(payload: SpaceIn, session: Session = Depends(get_db)) -> Space:
    """Dona d'alta un espai"""

    if payload.parent_id is not None and session.get(Space, payload.parent_id) is None:
        raise HTTPException(status_code=422, detail="L'espai pare no existix")

    space = Space(name=payload.name, type=payload.type, parent_id=payload.parent_id)
    session.add(space)
    session.commit()
    session.refresh(space)
    return space

@router.get(
    "/{space_id}/readings",
    response_model=list[ReadingSummaryOut] | list[ReadingBucketOut],
)
def space_readings(
    space_id: int,
    session: Session = Depends(get_db),
    start: datetime | None = Query(default=None, alias="from"),
    end: datetime | None = Query(default=None, alias="to"),
    bucket: str | None = Query(default=None, description=f"Un de: {', '.join(BUCKETS)}"),
) -> list[dict]:
    """Agrega les lectures dels dispositius d'un espai"""
    
    if session.get(Space, space_id) is None:
        raise HTTPException(status_code=404, detail="espai no trobat")

    if start is not None and end is not None and start >= end:
        raise HTTPException(status_code=422, detail="'from' ha de ser anterior a 'to'")

    if bucket is None:
        return summarize(session, [space_id], start, end)

    if bucket not in BUCKETS:
        raise HTTPException(
            status_code=422, detail=f"interval no suportat; opcions: {', '.join(BUCKETS)}"
        )

    return series(session, [space_id], bucket, start, end)