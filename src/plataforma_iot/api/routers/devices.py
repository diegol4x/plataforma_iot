"""Endpoints de dispositius"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from plataforma_iot.api.schemas import DeviceOut
from plataforma_iot.db import get_db
from plataforma_iot.models.device import Device


router = APIRouter(prefix="/devices", tags=["devices"])

@router.get("", response_model=list[DeviceOut])
def list_devices( 
    session: Session = Depends(get_db),
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Device]:
    """Torna la llista de dispositius coneguts, opcionalment filtrats per estat"""
    query = select(Device).order_by(Device.source, Device.device_id)

    if status is not None:
        query = query.where(Device.status == status)

    return list(session.scalars(query.limit(limit).offset(offset)))


@router.get("/{source}/{device_id}", response_model=DeviceOut)
def get_device(
    source: str,
    device_id: str,
    session: Session = Depends(get_db),
) -> Device:
    """Torna un dispositiu per la seua identitat completa"""
    device = session.get(Device, (source, device_id))
    if device is None:
        raise HTTPException(status_code=404, detail="dispositiu no trobat")
    return device
