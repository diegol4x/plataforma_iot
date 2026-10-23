"""Esquemes GET de telemetria."""

from datetime import datetime
from uuid import UUID

from pydantic import AliasPath, Field, BaseModel

from plataforma_iot.api.schemas.base import OutSchema


class ReadingOut(OutSchema):
    """Lectura"""

    id: UUID
    time: datetime
    uplink_id: UUID
    sensor_id: int
    value: float
    unit: str | None = Field(
        default=None,
        validation_alias=AliasPath("sensor", "sensor_type", "unit", "symbol"),
    )
    received_unit: str | None
    invalid_message: str | None

class ReadingSummaryOut(BaseModel):
    """Resum d'una magnitud en un rang"""

    name: str
    unit: str
    avg: float
    min: float
    max: float
    count: int


class ReadingBucketOut(ReadingSummaryOut):
    """Resum d'una magnitud en un interval de temps"""

    bucket: datetime

class DiscardOut(OutSchema):
    """Missatge descartat"""

    id: UUID
    received_at: datetime
    topic: str
    source: str | None
    device_id: str | None
    reason: str

class DiscardDetailOut(DiscardOut):
    """Un missatge descartat en concret (amb més detall)"""

    raw_payload: str
    detail: dict | None