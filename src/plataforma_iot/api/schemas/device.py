"""Esquema GET de dispositiu"""

from datetime import datetime
from pydantic import Field

from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.api.schemas.base import OutSchema, InSchema

class DeviceOut(OutSchema):
    """Esquema dispositiu"""

    source: str
    device_id: str
    name: str | None
    type: str
    status: str
    battery_level: int | None
    last_seen: datetime | None
    space_id: int | None

class DeviceProvisionIn(InSchema):
    """Dades per a provisionar un dispositiu"""

    name: str = Field(min_length=1, max_length=128)
    space_id: int | None = None
    status: DeviceStatus = DeviceStatus.ACTIVE