"""Models de dades de la plataforma.

Aquest mòdul importa totes les taules perquè queden registrades en
`Base.metadata`. Si un model no s'importa no apareix en les
migracions generades per Alembic. 
"""

from plataforma_iot.models.base import Base
from plataforma_iot.models.catalog import SensorType, Unit
from plataforma_iot.models.device import Device
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.space import Space
from plataforma_iot.models.telemetry import Uplink, Reading, Discard
from plataforma_iot.models.user import User
from plataforma_iot.models.workgroup import Workgroup

__all__ = ["Base", "Device", "Discard", "Reading", "Sensor", "SensorType", "Space", "Unit", "Uplink", "User", "Workgroup"]