"""Endpoints d'uplinks. Només per a administradors"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, Response
from plataforma_iot.api.dependencies import paginate, require_admin
from sqlalchemy import select
from sqlalchemy.orm import Session
from plataforma_iot.api.schemas import UplinkOut
from plataforma_iot.db import get_db
from plataforma_iot.models.telemetry import Uplink

router = APIRouter(
    prefix="/uplinks",
    tags=["uplinks"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[UplinkOut])
def list_uplinks(
    response: Response,
    session: Session = Depends(get_db),
    source: str | None = None,
    device_id: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Uplink]:
    """Llista els uplinks rebuts, dels més recents als més antics"""

    query = select(Uplink).order_by(Uplink.time.desc())

    if source is not None:
        query = query.where(Uplink.source == source)
    if device_id is not None:
        query = query.where(Uplink.device_id == device_id)
    if since is not None:
        query = query.where(Uplink.time >= since)
    if until is not None:
        query = query.where(Uplink.time < until)

    return paginate(session, query, response, limit, offset)


@router.get("/{uplink_id}", response_model=UplinkOut)
def get_uplink(uplink_id: UUID, session: Session = Depends(get_db)) -> Uplink:
    """Recupera un uplink pel seu identificador"""
    uplink = session.scalar(select(Uplink).where(Uplink.id == uplink_id))

    if uplink is None:
        raise HTTPException(status_code=404, detail="Uplink no trobat")

    return uplink