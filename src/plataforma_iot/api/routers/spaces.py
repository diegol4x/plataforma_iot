"""Endpoints d'espai"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from plataforma_iot.api.dependencies import current_user, require_admin
from plataforma_iot.api.schemas import (
    SpaceIn, 
    SpaceOut, 
    SpaceUpdateIn,
    ReadingBucketOut, 
    ReadingSummaryOut, 
    DeviceOut,
)
from plataforma_iot.db import get_db
from plataforma_iot.models.space import Space
from plataforma_iot.models.project import Project
from plataforma_iot.models.device import Device
from plataforma_iot.api.queries.readings import BUCKETS, series, summarize, descendant_ids

router = APIRouter(
    prefix="/spaces",
    tags=["spaces"],
    dependencies=[Depends(current_user)],
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
    """Dona d'alta un espai dins d'un projecte"""

    if session.get(Project, payload.project_id) is None:
        raise HTTPException(status_code=422, detail="El projecte no existix")

    if payload.parent_id is not None and session.get(Space, payload.parent_id) is None:
        raise HTTPException(status_code=422, detail="L'espai pare no existix")

    space = Space(
        name=payload.name,
        type=payload.type,
        parent_id=payload.parent_id,
        project_id=payload.project_id,
    )
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
    include_descendants: bool = Query(default=False, description="Inclou també els espais continguts"),
) -> list[dict]:
    """Agrega les lectures dels dispositius d'un espai"""

    if session.get(Space, space_id) is None:
        raise HTTPException(status_code=404, detail="Espai no trobat")

    if start is not None and end is not None and start >= end:
        raise HTTPException(status_code=422, detail="'from' ha de ser anterior a 'to'")

    if bucket is not None and bucket not in BUCKETS:
        raise HTTPException(
            status_code=422, detail=f"Interval no suportat; opcions: {', '.join(BUCKETS)}"
        )

    space_ids = descendant_ids(session, space_id) if include_descendants else [space_id]

    if bucket is None:
        return summarize(session, space_ids, start, end)

    return series(session, space_ids, bucket, start, end)


@router.get("/{space_id}/devices", response_model=list[DeviceOut])
def space_devices(
    space_id: int,
    session: Session = Depends(get_db),
    include_descendants: bool = Query(
        default=False, description="Inclou també els espais continguts"
    ),
) -> list[Device]:
    """Torna els dispositius ubicats en un espai"""

    if session.get(Space, space_id) is None:
        raise HTTPException(status_code=404, detail="Espai no trobat")

    space_ids = descendant_ids(session, space_id) if include_descendants else [space_id]

    query = (
        select(Device)
        .where(Device.space_id.in_(space_ids))
        .order_by(Device.source, Device.device_id)
    )

    return list(session.scalars(query))



@router.patch(
    "/{space_id}",
    response_model=SpaceOut,
    dependencies=[Depends(require_admin)],
)
def update_space(
    space_id: int,
    payload: SpaceUpdateIn,
    session: Session = Depends(get_db),
) -> Space:
    """Modifica un espai: nom, tipus o ubicació dins de la jerarquia."""

    space = session.get(Space, space_id)
    if space is None:
        raise HTTPException(status_code=404, detail="Espai no trobat")

    data = payload.model_dump(exclude_unset=True)

    if "parent_id" in data:
        _check_new_parent(session, space_id, data["parent_id"])

    for field, value in data.items():
        setattr(space, field, value)

    session.commit()
    session.refresh(space)
    return space


def _check_new_parent(session: Session, space_id: int, parent_id: int | None) -> None:
    """Comprova que el nou pare existix i que no crea un cicle."""

    if parent_id is None:
        return

    if parent_id == space_id:
        raise HTTPException(status_code=422, detail="Un espai no pot ser el seu propi pare")

    if session.get(Space, parent_id) is None:
        raise HTTPException(status_code=422, detail="L'espai pare no existix")

    if parent_id in descendant_ids(session, space_id):
        raise HTTPException(
            status_code=422, detail="El nou pare és un descendent d'este espai"
        )