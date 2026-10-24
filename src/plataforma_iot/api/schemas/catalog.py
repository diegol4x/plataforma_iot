"""Esquemes del catàleg"""

from pydantic import Field, AliasPath

from plataforma_iot.api.schemas.base import InSchema, OutSchema


class UnitIn(InSchema):
    """Alta d'una unitat de mesura"""

    name: str = Field(min_length=1, max_length=64)
    symbol: str = Field(min_length=1, max_length=16)


class SensorTypeIn(InSchema):
    """Alta d'una magnitud"""

    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    unit_symbol: str = Field(min_length=1, max_length=16)
    range_min: float | None = None
    range_max: float | None = None

class UnitOut(OutSchema):
    """Lectura d'una unitat de mesura"""

    id: int
    name: str
    symbol: str

class SensorTypeOut(OutSchema):
    """Magnitud del catàleg"""

    id: int
    code: str
    name: str
    unit: str = Field(validation_alias=AliasPath("unit", "symbol"))
    range_min: float | None
    range_max: float | None


class SensorTypeUpdateIn(InSchema):
    """Modificació d'una magnitud"""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    unit_symbol: str | None = Field(default=None, min_length=1, max_length=16)
    range_min: float | None = None
    range_max: float | None = None