"""Esquemes d'espai"""

from pydantic import Field

from plataforma_iot.domain.space_type import SpaceType
from plataforma_iot.api.schemas.base import OutSchema, InSchema


class SpaceIn(InSchema):
    """Alta d'un espai"""

    name: str = Field(min_length=1, max_length=128)
    type: str = Field(min_length=1, max_length=32)
    parent_id: int | None = None
    project_id: int

class SpaceOut(OutSchema):
    """Espai"""

    id: int
    name: str
    type: SpaceType
    parent_id: int | None
    project_id: int
    device_count: int = 0
    adjacent_ids: list[int] = []

class SpaceUpdateIn(InSchema):
    """Modificació d'un espai"""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    type: str | None = Field(default=None, min_length=1, max_length=32)
    parent_id: int | None = None