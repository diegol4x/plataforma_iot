"""Endpoints de sensors"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from plataforma_iot.api.dependencies import current_user, paginate, require_admin
from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session, joinedload

from plataforma_iot.api.schemas import SensorOut, SensorUpdateIn
from plataforma_iot.api.permissions import visible_device_identities
from plataforma_iot.db import get_db
from plataforma_iot.models.catalog import SensorType
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.user import User

router = APIRouter(
    prefix="/sensors",
    tags=["sensors"],
    dependencies=[Depends(current_user)],
    )


def _base_query():
    """Consulta amb el tipus i la unitat ja carregats"""
    return select(Sensor).options(
        joinedload(Sensor.sensor_type).joinedload(SensorType.unit)
    )


@router.get("", response_model=list[SensorOut])
def list_sensors(
    response: Response,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
    source: str | None = None,
    device_id: str | None = None,
    active: bool | None = None,
    pending: bool | None = Query(
        default=None,
        description="True: sols sensors amb la magnitud sense catalogar",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Sensor]:
    """Llista els sensors dels dispositius visibles per a l'usuari"""

    query = _base_query().order_by(Sensor.id)

    identities = visible_device_identities(session, user)
    if identities is not None:
        query = query.where(tuple_(Sensor.source, Sensor.device_id).in_(identities))

    if source is not None:
        query = query.where(Sensor.source == source)
    if device_id is not None:
        query = query.where(Sensor.device_id == device_id)
    if active is not None:
        query = query.where(Sensor.active == active)
    if pending is True:
        query = query.where(Sensor.sensor_type_id.is_(None))
    elif pending is False:
        query = query.where(Sensor.sensor_type_id.is_not(None))

    return paginate(session, query, response, limit, offset)


@router.get("/{sensor_id}", response_model=SensorOut)
def get_sensor(
    sensor_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> Sensor:
    """Recupera un sensor pel seu identificador"""

    sensor = session.scalar(_base_query().where(Sensor.id == sensor_id))

    identities = visible_device_identities(session, user)
    if sensor is None or (
        identities is not None and (sensor.source, sensor.device_id) not in identities
    ):
        raise HTTPException(status_code=404, detail="Sensor no trobat")

    return sensor

@router.patch("/{sensor_id}", response_model=SensorOut)
def update_sensor(
    sensor_id: int,
    payload: SensorUpdateIn,
    user: User = Depends(require_admin),
    session: Session = Depends(get_db),
) -> Sensor:
    """Modifica el nom d'un sensor o l'activa i el desactiva"""

    sensor = session.scalar(_base_query().where(Sensor.id == sensor_id))

    identities = visible_device_identities(session, user)
    if sensor is None or (
        identities is not None and (sensor.source, sensor.device_id) not in identities
    ):
        raise HTTPException(status_code=404, detail="Sensor no trobat")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sensor, field, value)

    session.commit()
    session.refresh(sensor)
    return sensor