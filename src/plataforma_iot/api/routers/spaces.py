"""Endpoints d'espai"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from plataforma_iot.api.dependencies import current_user, delete_or_409
from plataforma_iot.api.permissions import (
    can_assign_device_to_space,
    can_write_project,
    can_write_space,
    visible_device_identities,
    visible_project_ids,
)
from plataforma_iot.api.queries.readings import BUCKETS, descendant_ids, series, summarize
from plataforma_iot.api.queries.space_adjacency import neighbours, ordered_pair
from plataforma_iot.api.schemas import (
    DeviceOut,
    ReadingBucketOut,
    ReadingSummaryOut,
    SpaceIn,
    SpaceOut,
    SpaceUpdateIn,
)
from plataforma_iot.db import get_db
from plataforma_iot.models.device import Device
from plataforma_iot.models.project import Project
from plataforma_iot.models.space import Space, device_space, space_adjacency
from plataforma_iot.models.user import User

router = APIRouter(
    prefix="/spaces",
    tags=["spaces"],
    dependencies=[Depends(current_user)],
)


@router.get("", response_model=list[SpaceOut])
def list_spaces(
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> list[dict]:
    """Torna els espais visibles amb els seus dispositius i adjacències"""
    devices = (
        select(func.count())
        .select_from(device_space)
        .where(device_space.c.space_id == Space.id)
        .scalar_subquery()
    )

    query = select(Space, devices).order_by(Space.id)

    projects = visible_project_ids(session, user)
    if projects is not None:
        query = query.where(Space.project_id.in_(projects))

    rows = list(session.execute(query))
    space_ids = [space.id for space, _ in rows]

    # L'adjacència es guarda una sola volta amb a_id < b_id, així que cal
    # recórrer les dues columnes per a muntar els veïns de cada espai.
    by_space: dict[int, list[int]] = {space_id: [] for space_id in space_ids}

    for a_id, b_id in session.execute(
        select(space_adjacency).where(
            or_(
                space_adjacency.c.a_id.in_(space_ids),
                space_adjacency.c.b_id.in_(space_ids),
            )
        )
    ):
        if a_id in by_space:
            by_space[a_id].append(b_id)
        if b_id in by_space:
            by_space[b_id].append(a_id)

    return [
        {
            "id": space.id,
            "name": space.name,
            "type": space.type,
            "parent_id": space.parent_id,
            "project_id": space.project_id,
            "device_count": device_count,
            "adjacent_ids": by_space[space.id],
        }
        for space, device_count in rows
    ]


@router.post("", response_model=SpaceOut, status_code=201)
def create_space(
    payload: SpaceIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> Space:
    """Dona d'alta un espai dins d'un projecte.

    Qui el crea ha de ser propietari del projecte: un espai no té propietat
    pròpia, la hereta del projecte que el conté.
    """

    project = session.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=422, detail="El projecte no existix")

    if not can_write_project(user, project):
        raise HTTPException(
            status_code=403, detail="Només el propietari del projecte pot crear-hi espais"
        )

    if payload.parent_id is not None:
        parent = session.get(Space, payload.parent_id)
        if parent is None:
            raise HTTPException(status_code=422, detail="L'espai pare no existix")
        if parent.project_id != payload.project_id:
            raise HTTPException(
                status_code=422,
                detail="L'espai pare ha de ser del mateix projecte",
            )

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


@router.get("/{space_id}", response_model=SpaceOut)
def get_space(
    space_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> Space:
    """Torna un espai donat un id"""

    return _visible_space(session, user, space_id)


@router.patch("/{space_id}", response_model=SpaceOut)
def update_space(
    space_id: int,
    payload: SpaceUpdateIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> Space:
    """Modifica un espai: nom, tipus o ubicació dins de la jerarquia."""

    space = _visible_space(session, user, space_id)

    if not can_write_space(user, space):
        raise HTTPException(
            status_code=403, detail="Només el propietari del projecte pot modificar l'espai"
        )

    data = payload.model_dump(exclude_unset=True)

    if "parent_id" in data:
        _check_new_parent(session, space, data["parent_id"])

    for field, value in data.items():
        setattr(space, field, value)

    session.commit()
    session.refresh(space)
    return space


@router.get(
    "/{space_id}/readings",
    response_model=list[ReadingSummaryOut] | list[ReadingBucketOut],
)
def space_readings(
    space_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
    start: datetime | None = Query(default=None, alias="from"),
    end: datetime | None = Query(default=None, alias="to"),
    bucket: str | None = Query(default=None, description=f"Un de: {', '.join(BUCKETS)}"),
    include_descendants: bool = Query(
        default=False, description="Inclou també els espais continguts"
    ),
) -> list[dict]:
    """Agrega les lectures dels dispositius d'un espai"""

    _visible_space(session, user, space_id)

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
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
    include_descendants: bool = Query(
        default=False, description="Inclou també els espais continguts"
    ),
) -> list[Device]:
    """Torna els dispositius ubicats en un espai"""

    _visible_space(session, user, space_id)

    space_ids = descendant_ids(session, space_id) if include_descendants else [space_id]

    query = (
        select(Device)
        .join(
            device_space,
            (Device.source == device_space.c.source)
            & (Device.device_id == device_space.c.device_id),
        )
        .where(device_space.c.space_id.in_(space_ids))
        .order_by(Device.source, Device.device_id)
    )

    return list(session.scalars(query))


@router.put("/{space_id}/devices/{source}/{device_id}", status_code=204)
def assign_device(
    space_id: int,
    source: str,
    device_id: str,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> None:
    """Ubica un dispositiu en un espai.

    Dins d'un mateix projecte un dispositiu sols pot estar en un espai: si ja
    estava en un altre del mateix projecte, es mou. Els espais d'altres
    projectes no es toquen.
    """

    space = _visible_space(session, user, space_id)
    device = _visible_device(session, user, source, device_id)

    if not can_assign_device_to_space(user, device, space):
        raise HTTPException(
            status_code=403, detail="No pots ubicar este dispositiu en este espai"
        )

    for current in list(device.spaces):
        if current.project_id == space.project_id and current.id != space.id:
            device.spaces.remove(current)

    if space not in device.spaces:
        device.spaces.append(space)

    session.commit()


@router.delete("/{space_id}/devices/{source}/{device_id}", status_code=204)
def unassign_device(
    space_id: int,
    source: str,
    device_id: str,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> None:
    """Trau un dispositiu de l'espai. Si no hi era, no fa res."""

    space = _visible_space(session, user, space_id)
    device = _visible_device(session, user, source, device_id)

    if not can_assign_device_to_space(user, device, space):
        raise HTTPException(
            status_code=403, detail="No pots modificar la ubicació d'este dispositiu"
        )

    if space in device.spaces:
        device.spaces.remove(space)
        session.commit()


def _check_new_parent(session: Session, space: Space, parent_id: int | None) -> None:
    """Comprova que el nou pare existix, és del mateix projecte i no crea un cicle."""

    if parent_id is None:
        return

    if parent_id == space.id:
        raise HTTPException(status_code=422, detail="Un espai no pot ser el seu propi pare")

    parent = session.get(Space, parent_id)
    if parent is None:
        raise HTTPException(status_code=422, detail="L'espai pare no existix")

    if parent.project_id != space.project_id:
        raise HTTPException(
            status_code=422, detail="L'espai pare ha de ser del mateix projecte"
        )

    if parent_id in descendant_ids(session, space.id):
        raise HTTPException(
            status_code=422, detail="El nou pare és un descendent d'este espai"
        )


def _visible_space(session: Session, user: User, space_id: int) -> Space:
    """Recupera un espai comprovant que l'usuari el pot veure.

    Un espai d'un projecte alié dona 404, no 403: un 403 en confirmaria
    l'existència.
    """
    space = session.get(Space, space_id)

    projects = visible_project_ids(session, user)
    if space is None or (projects is not None and space.project_id not in projects):
        raise HTTPException(status_code=404, detail="Espai no trobat")

    return space


def _visible_device(session: Session, user: User, source: str, device_id: str) -> Device:
    """Recupera un dispositiu comprovant que l'usuari el pot veure."""

    device = session.get(Device, (source, device_id))

    identities = visible_device_identities(session, user)
    if device is None or (identities is not None and (source, device_id) not in identities):
        raise HTTPException(status_code=404, detail="Dispositiu no trobat")

    return device

@router.delete("/{space_id}", status_code=204)
def delete_space(
    space_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> None:
    """Esborra un espai sense fills. Només el propietari del projecte."""

    space = _visible_space(session, user, space_id)

    if not can_write_space(user, space):
        raise HTTPException(
            status_code=403, detail="Només el propietari del projecte pot esborrar l'espai"
        )

    delete_or_409(session, space, "L'espai encara conté altres espais")

@router.get("/{space_id}/adjacent", response_model=list[SpaceOut])
def list_adjacent(
    space_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> list[Space]:
    """Torna els espais adjacents a un altre"""

    _visible_space(session, user, space_id)
    return neighbours(session, space_id)


@router.put("/{space_id}/adjacent/{other_id}", status_code=204)
def add_adjacency(
    space_id: int,
    other_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> None:
    """Declara que dos espais són adjacents.

    L'adjacència és simètrica, així que l'ordre dels dos identificadors no
    importa: es guarda una sola volta, sempre amb el menor primer.
    """

    space = _visible_space(session, user, space_id)
    other = _visible_space(session, user, other_id)

    if space.id == other.id:
        raise HTTPException(
            status_code=422, detail="Un espai no pot ser adjacent a si mateix"
        )

    # Invariant d'aplicació, no d'esquema: un CHECK no pot mirar el project_id
    # d'una altra taula, i un trigger afegiria lògica en SQL que no compensa.
    if space.project_id != other.project_id:
        raise HTTPException(
            status_code=422, detail="Els dos espais han de ser del mateix projecte"
        )

    if not can_write_space(user, space):
        raise HTTPException(
            status_code=403,
            detail="Només el propietari del projecte pot declarar adjacències",
        )

    a_id, b_id = ordered_pair(space.id, other.id)

    exists = session.scalar(
        select(space_adjacency).where(
            space_adjacency.c.a_id == a_id, space_adjacency.c.b_id == b_id
        )
    )
    if exists is None:
        session.execute(space_adjacency.insert().values(a_id=a_id, b_id=b_id))
        session.commit()


@router.delete("/{space_id}/adjacent/{other_id}", status_code=204)
def remove_adjacency(
    space_id: int,
    other_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> None:
    """Trau l'adjacència entre dos espais. Si no n'hi havia, no fa res."""

    space = _visible_space(session, user, space_id)
    other = _visible_space(session, user, other_id)

    if not can_write_space(user, space):
        raise HTTPException(
            status_code=403,
            detail="Només el propietari del projecte pot llevar adjacències",
        )

    a_id, b_id = ordered_pair(space.id, other.id)

    session.execute(
        space_adjacency.delete().where(
            space_adjacency.c.a_id == a_id, space_adjacency.c.b_id == b_id
        )
    )
    session.commit()