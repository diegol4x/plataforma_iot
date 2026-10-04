"""Esquemes de GET de l'API."""

from plataforma_iot.api.schemas.base import OutSchema
from plataforma_iot.api.schemas.device import DeviceOut, DeviceProvisionIn
from plataforma_iot.api.schemas.sensor import SensorOut
from plataforma_iot.api.schemas.telemetry import DiscardDetailOut, DiscardOut, ReadingOut, ReadingBucketOut, ReadingSummaryOut
from plataforma_iot.api.schemas.catalog import UnitIn, SensorTypeIn, UnitOut, SensorTypeOut
from plataforma_iot.api.schemas.auth import TokenOut
from plataforma_iot.api.schemas.space import SpaceIn, SpaceOut

__all__ = [
    "DeviceOut",
    "DiscardDetailOut",
    "DiscardOut",
    "OutSchema",
    "ReadingOut",
    "SensorOut",
    "DeviceProvisionIn",
    "UnitIn",
    "SensorTypeIn",
    "UnitOut",
    "SensorTypeOut",
    "TokenOut",
    "SpaceIn",
    "SpaceOut",
    "ReadingBucketOut",
    "ReadingSummaryOut",
]