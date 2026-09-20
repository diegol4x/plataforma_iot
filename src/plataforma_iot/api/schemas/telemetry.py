"""Esquemes GET de telemetria."""

from datetime import datetime
from uuid import UUID

from pydantic import AliasPath, Field

from plataforma_iot.api.schemas.base import OutSchema


class ReadingOut(OutSchema):
    """Lectura"""

    id: UUID
    time: datetime
    uplink_id: UUID
    sensor_id: int
    value: float
    unit: str = Field(validation_alias=AliasPath("sensor", "sensor_type", "unit", "symbol"))
    received_unit: str | None

class DiscardOut(OutSchema):
    """Missatge descartat"""

    id: UUID
    received_at: datetime
    topic: str
    reason: str

class DiscardDetailOut(DiscardOut):
    """Un missatge descartat en concret (amb més detall)"""

    raw_payload: str
    detail: dict | None