"""Estats d'un dispositiu."""

from enum import StrEnum

class DeviceStatus(StrEnum):
    """Estat d'un dispositiu"""

    UNPROVISIONED = "unprovisioned" # Quan es descobrix automàticament, pasa a active sols quan s'activa manualment
    ACTIVE = "active" # Si pasa cert temps es sense parlar es desactiva
    SILENT = "silent" # Si parla s'activa
    RETIRED = "retired" # ACTIVE/SILENT -> RETIRED (Unidireccional)
