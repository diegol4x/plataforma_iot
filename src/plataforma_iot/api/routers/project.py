"""Endpoints de projectes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from plataforma_iot.api.dependencies import current_user
from plataforma_iot.api.permissions import (
    can_write_project,
    visible_project_ids,
    workgroup_ids,
)
from plataforma_iot.api.schemas import ProjectIn, ProjectOut, ProjectUpdateIn
from plataforma_iot.db import get_db
from plataforma_iot.domain.user_role import UserRole
from plataforma_iot.models.project import Project
from plataforma_iot.models.user import User
from plataforma_iot.models.workgroup import Workgroup

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(current_user)],
)


@router.get("", response_model=list[ProjectOut])
def list_projects(
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> list[Project]:
    """Torna els projectes dels grups de l'usuari"""

    query = select(Project).order_by(Project.name)

    projects = visible_project_ids(session, user)
    if projects is not None:
        query = query.where(Project.id.in_(projects))

    return list(session.scalars(query))


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> Project:
    """Crea un projecte dins d'un grup. Qui el crea n'esdevé propietari."""

    if session.get(Workgroup, payload.workgroup_id) is None:
        raise HTTPException(status_code=422, detail="El grup no existix")

    if user.role is not UserRole.ADMIN and payload.workgroup_id not in workgroup_ids(user):
        raise HTTPException(
            status_code=403, detail="No pertanys a este grup de treball"
        )

    clash = session.scalar(
        select(Project).where(
            Project.workgroup_id == payload.workgroup_id, Project.name == payload.name
        )
    )
    if clash is not None:
        raise HTTPException(
            status_code=409, detail=f"El grup ja té un projecte '{payload.name}'"
        )

    project = Project(
        name=payload.name,
        description=payload.description,
        workgroup_id=payload.workgroup_id,
        owner_id=user.id,
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> Project:
    """Torna un projecte"""

    return _visible_project(session, user, project_id)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectUpdateIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> Project:
    """Modifica un projecte. Només el propietari o un admin."""

    project = _visible_project(session, user, project_id)

    if not can_write_project(user, project):
        raise HTTPException(
            status_code=403, detail="Només el propietari pot modificar el projecte"
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    session.commit()
    session.refresh(project)
    return project


def _visible_project(session: Session, user: User, project_id: int) -> Project:
    """Recupera un projecte comprovant que l'usuari el pot veure."""

    project = session.get(Project, project_id)

    projects = visible_project_ids(session, user)
    if project is None or (projects is not None and project.id not in projects):
        raise HTTPException(status_code=404, detail="Projecte no trobat")

    return project