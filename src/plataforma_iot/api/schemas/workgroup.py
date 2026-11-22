"""Esquemes de grups de treballs"""

from pydantic import Field

from plataforma_iot.api.schemas.base import OutSchema, InSchema

class WorkgroupIn(InSchema):
    """Alta d'un grup de treball."""

    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=255)


class WorkgroupUpdateIn(InSchema):
    """Modificació d'un grup de treball."""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=255)


class WorkgroupOut(OutSchema):
    """Grup de treball"""

    id: int
    name: str
    description: str | None
    member_count: int = 0
    device_count: int = 0