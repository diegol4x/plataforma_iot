"""Esquemes GET de sensor"""
from pydantic import AliasPath, Field

from plataforma_iot.api.schemas.base import OutSchema


class SensorOut(OutSchema):
    """Sensor"""

    id: int
    source: str
    device_id: str
    name: str
    active: bool
    
    sensor_type_code: str | None = Field(
        default=None, validation_alias=AliasPath("sensor_type", "code")
    )
    sensor_type_name: str | None = Field(
        default=None, validation_alias=AliasPath("sensor_type", "name")
    )
    unit: str | None = Field(
        default=None, validation_alias=AliasPath("sensor_type", "unit", "symbol")
    )