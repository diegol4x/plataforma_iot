"""Esquema GET de dispositiu"""

from datetime import datetime
from pydantic import Field, field_validator

from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.api.schemas.base import OutSchema, InSchema

class DeviceOut(OutSchema):
    """Esquema dispositiu"""

    source: str
    device_id: str
    name: str | None
    type: str | None
    status: str
    battery_level: int | None
    last_seen: datetime | None
    space_ids: list[int] = Field(default_factory=list, validation_alias="spaces")

    @field_validator("space_ids", mode="before")
    @classmethod
    def _ids_only(cls, spaces: list) -> list[int]:
        return [space.id if hasattr(space, "id") else space for space in spaces]

class DeviceProvisionIn(InSchema):
    """Dades per a provisionar un dispositiu"""

    name: str = Field(min_length=1, max_length=128)
    type: str | None = Field(default=None, max_length=32)
    status: DeviceStatus = DeviceStatus.ACTIVE