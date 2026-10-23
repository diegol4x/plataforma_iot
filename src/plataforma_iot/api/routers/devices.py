"""Endpoints de dispositius"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session

from plataforma_iot.api.dependencies import current_user, require_admin
from plataforma_iot.api.permissions import visible_device_identities
from plataforma_iot.api.schemas import DeviceOut, DeviceProvisionIn
from plataforma_iot.db import get_db
from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.models.device import Device
from plataforma_iot.models.space import Space
from plataforma_iot.models.user import User


router = APIRouter(
    prefix="/devices",
    tags=["devices"],
    dependencies=[Depends(current_user)],
    )

@router.get("", response_model=list[DeviceOut])
def list_devices(
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
    status: DeviceStatus | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Device]:
    """Torna els dispositius visibles per a l'usuari, opcionalment per estat"""

    query = select(Device).order_by(Device.source, Device.device_id)

    identities = visible_device_identities(session, user)
    if identities is not None:
        query = query.where(
            tuple_(Device.source, Device.device_id).in_(identities)
        )

    if status is not None:
        query = query.where(Device.status == status)

    return list(session.scalars(query.limit(limit).offset(offset)))


@router.get("/{source}/{device_id}", response_model=DeviceOut)
def get_device(
    source: str,
    device_id: str,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> Device:
    """Torna un dispositiu per la seua identitat completa"""

    device = session.get(Device, (source, device_id))

    identities = visible_device_identities(session, user)
    if device is None or (identities is not None and (source, device_id) not in identities):
        raise HTTPException(status_code=404, detail="Dispositiu no trobat")

    return device


@router.patch(
        "/{source}/{device_id}",
        response_model=DeviceOut,
        dependencies=[Depends(require_admin)],
        )

def provision_device(
    source: str,
    device_id: str,
    payload: DeviceProvisionIn,
    session: Session = Depends(get_db)
) -> Device:
    """Provisiona un dispositiu descobert o n'edita les dades"""

    device = session.get(Device, (source, device_id))
    if device is None:
        raise HTTPException(status_code=404, detail="Dispositiu no trobat")

    data = payload.model_dump(exclude_unset=True)
    new_status = data.pop("status", DeviceStatus.ACTIVE)

    if device.status is DeviceStatus.UNPROVISIONED:
        if new_status is not DeviceStatus.ACTIVE:
            raise HTTPException(
                status_code=409,
                detail="Un dispositiu desprovisionat només pot passar a \"active\"",
            )
        device.status = DeviceStatus.ACTIVE
    elif "status" in payload.model_fields_set:
        raise HTTPException(
            status_code=409,
            detail=f"L'estat '{device.status.value}' no es pot canviar manualment",
        )

    if data.get("space_id") is not None and session.get(Space, data["space_id"]) is None:
        raise HTTPException(status_code=422, detail="Espai no trobat")

    for field, value in data.items():
        setattr(device, field, value)

    session.commit()
    session.refresh(device)
    return device
