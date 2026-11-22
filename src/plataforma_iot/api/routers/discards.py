"""Endpoints de missatges rebutjats"""

from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from plataforma_iot.api.schemas import DiscardDetailOut, DiscardOut
from plataforma_iot.db import get_db
from plataforma_iot.models.telemetry import Discard
from plataforma_iot.api.dependencies import require_admin, paginate

router = APIRouter(
    prefix="/discards",
    tags=["discards"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[DiscardOut])
def list_discards(
    response: Response,
    session: Session = Depends(get_db),
    reason: str | None = None,
    source: str | None = None,
    device_id: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Discard]:
    """Llista els missatges rebutjats, opcionalment filtrats pel motiu"""

    query = select(Discard).order_by(Discard.received_at.desc())

    if reason is not None:
        query = query.where(Discard.reason == reason)
    if source is not None:
        query = query.where(Discard.source == source)
    if device_id is not None:
        query = query.where(Discard.device_id == device_id)
    if since is not None:
        query = query.where(Discard.received_at >= since)
    if until is not None:
        query = query.where(Discard.received_at < until)

    return paginate(session, query, response, limit, offset)


@router.get("/{discard_id}", response_model=DiscardDetailOut)
def get_discard(discard_id: UUID, session: Session = Depends(get_db)) -> Discard:
    """Recupera un descart amb el payload original"""
    discard = session.get(Discard, discard_id)
    if discard is None:
        raise HTTPException(status_code=404, detail="descart no trobat")
    return discard