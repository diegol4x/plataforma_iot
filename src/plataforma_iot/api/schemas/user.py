"""Esquemes d'Usuaris"""

from plataforma_iot.api.schemas.base import OutSchema
from plataforma_iot.domain.user_role import UserRole


class UserOut(OutSchema):
    """Usuari"""

    id: int
    username: str
    role: UserRole
    active: bool