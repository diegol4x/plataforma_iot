"""Endpoints del catàleg: unitats i tipus de sensor"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from plataforma_iot.api.schemas import SensorTypeIn, UnitIn, UnitOut, SensorTypeOut
from plataforma_iot.db import get_db
from plataforma_iot.models.catalog import SensorType, Unit
from plataforma_iot.api.dependencies import current_role, require_admin


router = APIRouter(
    tags=["catalog"],
    dependencies=[Depends(current_role)],
    )

@router.get("/units", response_model=list[UnitIn])
def list_units(session: Session = Depends(get_db)) -> list[Unit]:
    """Torna les unitats del catàleg"""

    return list(session.scalars(select(Unit).order_by(Unit.symbol)))

@router.post("/units", response_model=UnitOut, status_code=201, dependencies=[Depends(require_admin)],)
def create_unit(payload: UnitIn, session: Session = Depends(get_db)) -> Unit:
    """Dona d'alta una unitat de mesura"""

    existing = session.scalar(select(Unit).where(Unit.symbol == payload.symbol))

    if existing is not None:
        raise HTTPException(status_code=409, detail=f"La unitat '{payload.symbol}' ja existix")

    unit = Unit(name=payload.name, symbol=payload.symbol)
    session.add(unit)
    session.commit()
    session.refresh(unit)   
    return unit


@router.get("/sensor_types", response_model=list[SensorTypeOut])
def list_sensor_types(session: Session = Depends(get_db)) -> list[SensorType]:
    """Torna les magnituds del catàleg"""

    return list(session.scalars(select(SensorType).order_by(SensorType.code)))


@router.post("/sensor_types", response_model=SensorTypeOut, status_code=201, dependencies=[Depends(require_admin)],)
def create_sensor_type(payload: SensorTypeIn, session: Session = Depends(get_db)) -> SensorType:
    """Dona d'alta una magnitud amb unitat existent prèvia"""

    existing = session.scalar(select(SensorType).where(SensorType.code == payload.code))

    if existing is not None:
        raise HTTPException(status_code=409, detail=f"La magnitud '{payload.code}' ja existix")

    unit = session.scalar(select(Unit).where(Unit.symbol == payload.unit_symbol))

    if unit is None:
        raise HTTPException(
            status_code=422, detail=f"La unitat '{payload.unit_symbol}' no està al catàleg"
        )

    if (
        payload.range_min is not None
        and payload.range_max is not None
        and payload.range_min > payload.range_max
    ):
        raise HTTPException(status_code=422, detail="Range_min no pot superar range_max")

    sensor_type = SensorType(
        code=payload.code,
        name=payload.name,
        unit_id=unit.id,
        range_min=payload.range_min,
        range_max=payload.range_max,
    )

    session.add(sensor_type)
    session.commit()
    session.refresh(sensor_type)
    return sensor_type
