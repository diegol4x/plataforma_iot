"""Rols d'usuari de la plataforma"""

from enum import StrEnum

class UserRole(StrEnum):
    """Rol que determina què accions pot dur a terme un usuari"""

    VIEWER = "viewer"
    ADMIN = "admin"
