"""Esquema GET de dispositiu"""

from datetime import datetime

from plataforma_iot.api.schemas.base import OutSchema

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