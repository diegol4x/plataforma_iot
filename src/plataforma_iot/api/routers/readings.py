"""Endpoints de lectures"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session, joinedload

from plataforma_iot.api.schemas import ReadingOut
from plataforma_iot.db import get_db
from plataforma_iot.models.catalog import SensorType
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.telemetry import Reading
from plataforma_iot.api.dependencies import current_user
from plataforma_iot.api.permissions import visible_device_identities
from plataforma_iot.models.user import User


router = APIRouter(
    prefix="/readings",
    tags=["readings"],
    dependencies=[Depends(current_user)],
    )


@router.get("", response_model=list[ReadingOut])
def list_readings(
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
    sensor_id: int | None = None,
    source: str | None = None,
    device_id: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[Reading]:
    """Llista les lectures dels dispositius visibles per a l'usuari.

    El filtre va pel grup del DISPOSITIU, no per l'espai: la propietat del
    dispositiu és del grup, i un sensor encara sense ubicar no ha de ser
    invisible per als seus.
    """
    query = (
        select(Reading)
        .join(Sensor, Sensor.id == Reading.sensor_id)
        .options(
            joinedload(Reading.sensor)
            .joinedload(Sensor.sensor_type)
            .joinedload(SensorType.unit)
        )
        .order_by(Reading.time.desc())
    )

    identities = visible_device_identities(session, user)
    if identities is not None:
        query = query.where(tuple_(Sensor.source, Sensor.device_id).in_(identities))

    if sensor_id is not None:
        query = query.where(Reading.sensor_id == sensor_id)
    if source is not None:
        query = query.where(Sensor.source == source)
    if device_id is not None:
        query = query.where(Sensor.device_id == device_id)
    if since is not None:
        query = query.where(Reading.time >= since)
    if until is not None:
        query = query.where(Reading.time < until)
    
    return list(session.scalars(query.limit(limit).offset(offset)))