"""Esquemes de projectes"""

from pydantic import Field

from plataforma_iot.api.schemas.base import OutSchema, InSchema


class ProjectIn(InSchema):
    """Alta d'un projecte."""

    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=255)
    workgroup_id: int


class ProjectUpdateIn(InSchema):
    """Modificació d'un projecte."""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=255)


class ProjectOut(OutSchema):
    """Projecte"""

    id: int
    name: str
    description: str | None
    workgroup_id: int
    owner_id: int