"""Endpoints de grups de treball. Només per a administradors."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from plataforma_iot.api.dependencies import require_admin, delete_or_409
from plataforma_iot.api.schemas import (
    DeviceOut,
    UserOut,
    WorkgroupIn,
    WorkgroupOut,
    WorkgroupUpdateIn,
)
from plataforma_iot.db import get_db
from plataforma_iot.models.device import Device
from plataforma_iot.models.user import User
from plataforma_iot.models.workgroup import Workgroup

router = APIRouter(
    prefix="/workgroups",
    tags=["workgroups"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[WorkgroupOut])
def list_workgroups(session: Session = Depends(get_db)) -> list[Workgroup]:
    """Torna tots els grups de treball"""

    return list(session.scalars(select(Workgroup).order_by(Workgroup.name)))


@router.post("", response_model=WorkgroupOut, status_code=201)
def create_workgroup(payload: WorkgroupIn, session: Session = Depends(get_db)) -> Workgroup:
    """Dona d'alta un grup de treball"""

    existing = session.scalar(select(Workgroup).where(Workgroup.name == payload.name))
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"El grup '{payload.name}' ja existix")

    workgroup = Workgroup(name=payload.name, description=payload.description)
    session.add(workgroup)
    session.commit()
    session.refresh(workgroup)
    return workgroup


@router.get("/{workgroup_id}", response_model=WorkgroupOut)
def get_workgroup(workgroup_id: int, session: Session = Depends(get_db)) -> Workgroup:
    """Torna un grup de treball"""

    return _get_or_404(session, workgroup_id)


@router.patch("/{workgroup_id}", response_model=WorkgroupOut)
def update_workgroup(
    workgroup_id: int,
    payload: WorkgroupUpdateIn,
    session: Session = Depends(get_db),
) -> Workgroup:
    """Modifica el nom o la descripció d'un grup"""

    workgroup = _get_or_404(session, workgroup_id)
    data = payload.model_dump(exclude_unset=True)

    if "name" in data:
        clash = session.scalar(
            select(Workgroup).where(
                Workgroup.name == data["name"], Workgroup.id != workgroup_id
            )
        )
        if clash is not None:
            raise HTTPException(
                status_code=409, detail=f"El grup '{data['name']}' ja existix"
            )

    for field, value in data.items():
        setattr(workgroup, field, value)

    session.commit()
    session.refresh(workgroup)
    return workgroup


@router.get("/{workgroup_id}/members", response_model=list[UserOut])
def list_members(workgroup_id: int, session: Session = Depends(get_db)) -> list[User]:
    """Torna els membres d'un grup"""

    return _get_or_404(session, workgroup_id).members


@router.put("/{workgroup_id}/members/{user_id}", status_code=204)
def add_member(
    workgroup_id: int, user_id: int, session: Session = Depends(get_db)
) -> None:
    """Afig un usuari al grup. Si ja hi és, no fa res."""

    workgroup = _get_or_404(session, workgroup_id)

    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuari no trobat")

    if user not in workgroup.members:
        workgroup.members.append(user)
        session.commit()


@router.delete("/{workgroup_id}/members/{user_id}", status_code=204)
def remove_member(
    workgroup_id: int, user_id: int, session: Session = Depends(get_db)
) -> None:
    """Trau un usuari del grup. Si no hi era, no fa res."""

    workgroup = _get_or_404(session, workgroup_id)

    user = session.get(User, user_id)
    if user is not None and user in workgroup.members:
        workgroup.members.remove(user)
        session.commit()


@router.get("/{workgroup_id}/devices", response_model=list[DeviceOut])
def list_workgroup_devices(
    workgroup_id: int, session: Session = Depends(get_db)
) -> list[Device]:
    """Torna els dispositius assignats a un grup"""

    return _get_or_404(session, workgroup_id).devices


@router.put("/{workgroup_id}/devices/{source}/{device_id}", status_code=204)
def add_device(
    workgroup_id: int, source: str, device_id: str, session: Session = Depends(get_db)
) -> None:
    """Assigna un dispositiu al grup. Un dispositiu pot estar en diversos grups."""

    workgroup = _get_or_404(session, workgroup_id)

    device = session.get(Device, (source, device_id))
    if device is None:
        raise HTTPException(status_code=404, detail="Dispositiu no trobat")

    if device not in workgroup.devices:
        workgroup.devices.append(device)
        session.commit()


@router.delete("/{workgroup_id}/devices/{source}/{device_id}", status_code=204)
def remove_device(
    workgroup_id: int, source: str, device_id: str, session: Session = Depends(get_db)
) -> None:
    """Trau un dispositiu del grup, sense tocar els altres grups on estiga."""

    workgroup = _get_or_404(session, workgroup_id)

    device = session.get(Device, (source, device_id))
    if device is not None and device in workgroup.devices:
        workgroup.devices.remove(device)
        session.commit()


def _get_or_404(session: Session, workgroup_id: int) -> Workgroup:
    workgroup = session.get(Workgroup, workgroup_id)
    if workgroup is None:
        raise HTTPException(status_code=404, detail="Grup no trobat")
    return workgroup

@router.delete("/{workgroup_id}", status_code=204)
def delete_workgroup(workgroup_id: int, session: Session = Depends(get_db)) -> None:
    """Esborra un grup que no tinga projectes"""

    workgroup = _get_or_404(session, workgroup_id)
    delete_or_409(session, workgroup, "El grup encara té projectes")