"""Endpoints de lectures"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from plataforma_iot.api.schemas import ReadingOut
from plataforma_iot.db import get_db
from plataforma_iot.models.catalog import SensorType
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.telemetry import Reading
from plataforma_iot.api.dependencies import current_user, require_admin


router = APIRouter(
    prefix="/readings",
    tags=["readings"],
    dependencies=[Depends(current_user)],
    )


@router.get("", response_model=list[ReadingOut])
def list_readings(
    session: Session = Depends(get_db),
    sensor_id: int | None = None,
    source: str | None = None,
    device_id: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[Reading]:
    """Llista les lectures més recents dins dels filtres indicats"""
    query = (
        select(Reading)
        .options(joinedload(Reading.sensor).joinedload(Sensor.sensor_type).joinedload(SensorType.unit))
        .order_by(Reading.time.desc())
    )

    if sensor_id is not None:
        query = query.where(Reading.sensor_id == sensor_id)
    if source is not None or device_id is not None:
        query = query.join(Sensor, Sensor.id == Reading.sensor_id)
        if source is not None:
            query = query.where(Sensor.source == source)
        if device_id is not None:
            query = query.where(Sensor.device_id == device_id)
    if since is not None:
        query = query.where(Reading.time >= since)
    if until is not None:
        query = query.where(Reading.time < until)

    return list(session.scalars(query.limit(limit).offset(offset)))