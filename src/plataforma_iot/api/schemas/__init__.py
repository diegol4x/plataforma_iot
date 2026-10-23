"""Esquemes de GET de l'API."""

from plataforma_iot.api.schemas.base import OutSchema
from plataforma_iot.api.schemas.device import DeviceOut, DeviceProvisionIn
from plataforma_iot.api.schemas.sensor import SensorOut
from plataforma_iot.api.schemas.telemetry import DiscardDetailOut, DiscardOut, ReadingOut, ReadingBucketOut, ReadingSummaryOut
from plataforma_iot.api.schemas.catalog import UnitIn, SensorTypeIn, UnitOut, SensorTypeOut
from plataforma_iot.api.schemas.auth import TokenOut
from plataforma_iot.api.schemas.space import SpaceIn, SpaceOut, SpaceUpdateIn
from plataforma_iot.api.schemas.user import UserOut
from plataforma_iot.api.schemas.workgroup import WorkgroupIn, WorkgroupOut, WorkgroupUpdateIn
from plataforma_iot.api.schemas.projects import ProjectIn, ProjectOut, ProjectUpdateIn

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
    "SpaceUpdateIn",
    "WorkgroupIn",
    "WorkgroupOut",
    "WorkgroupUpdateIn",
    "UserOut",
    "ProjectIn",
    "ProjectOut",
    "ProjectUpdateIn",
]