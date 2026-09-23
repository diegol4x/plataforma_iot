"""Esquemes de GET de l'API."""

from plataforma_iot.api.schemas.base import OutSchema
from plataforma_iot.api.schemas.device import DeviceOut, DeviceProvisionIn
from plataforma_iot.api.schemas.sensor import SensorOut
from plataforma_iot.api.schemas.telemetry import DiscardDetailOut, DiscardOut, ReadingOut

__all__ = [
    "DeviceOut",
    "DiscardDetailOut",
    "DiscardOut",
    "OutSchema",
    "ReadingOut",
    "SensorOut",
    "DeviceProvisionIn",
]