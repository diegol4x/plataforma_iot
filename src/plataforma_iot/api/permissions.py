"""Regles d'autorització sobre projectes, espais i dispositius"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from plataforma_iot.domain.user_role import UserRole
from plataforma_iot.models.device import Device
from plataforma_iot.models.project import Project
from plataforma_iot.models.space import Space
from plataforma_iot.models.user import User
from plataforma_iot.models.workgroup import device_workgroup

def workgroup_ids(user: User) -> set[int]:
    """Grups als quals pertany l'usuari"""
    return {workgroup.id for workgroup in user.workgroups}


def can_read_project(user: User, project: Project) -> bool:
    """Veure un projecte: pertànyer al seu grup"""
    if user.role is UserRole.ADMIN:
        return True
    return project.workgroup_id in workgroup_ids(user)


def can_write_project(user: User, project: Project) -> bool:
    """Modificar un projecte: ser el propietari"""
    if user.role is UserRole.ADMIN:
        return True
    return project.owner_id == user.id


def can_read_space(user: User, space: Space) -> bool:
    """Veure un espai: poder veure el seu projecte"""
    return can_read_project(user, space.project)


def can_write_space(user: User, space: Space) -> bool:
    """Modificar un espai: ser propietari del seu projecte"""
    return can_write_project(user, space.project)


def can_assign_device_to_space(user: User, device: Device, space: Space) -> bool:
    """Ubicar un dispositiu: poder escriure a l'espai i tindre el dispositiu.

    El dispositiu ha de ser d'un grup de l'usuari, perquè la seua propietat és
    del grup i no de qui el col·loca
    """
    if user.role is UserRole.ADMIN:
        return True

    device_groups = {workgroup.id for workgroup in device.workgroups}
    return can_write_space(user, space) and bool(device_groups & workgroup_ids(user))

def visible_project_ids(session: Session, user: User) -> set[int] | None:
    """Projectes que l'usuari pot veure, o None si els pot veure tots.

    None significa "sense restricció": és el cas de l'admin, i permet que qui
    la crida no haja d'afegir cap WHERE en lloc d'afegir-ne un que ho inclou tot.
    """
    if user.role is UserRole.ADMIN:
        return None

    groups = workgroup_ids(user)
    if not groups:
        return set()

    return set(
        session.scalars(
            select(Project.id).where(Project.workgroup_id.in_(groups))
        )
    )


def visible_device_identities(session: Session, user: User) -> set[tuple[str, str]] | None:
    """Dispositius que l'usuari pot veure, o None si els pot veure tots.

    Un dispositiu sense grup no el veu cap viewer: acaba de ser descobert i
    encara no l'ha reclamat ningú.
    """
    if user.role is UserRole.ADMIN:
        return None

    groups = workgroup_ids(user)
    if not groups:
        return set()

    rows = session.execute(
        select(device_workgroup.c.source, device_workgroup.c.device_id).where(
            device_workgroup.c.workgroup_id.in_(groups)
        )
    )
    return {(source, device_id) for source, device_id in rows}