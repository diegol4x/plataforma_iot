"""Esquemes d'Usuaris"""

from pydantic import Field

from plataforma_iot.api.schemas.base import InSchema, OutSchema
from plataforma_iot.domain.user_role import UserRole

MIN_PASSWORD = 8


class UserIn(InSchema):
    """Alta d'un usuari"""

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=MIN_PASSWORD, max_length=128)
    role: UserRole = UserRole.VIEWER


class UserUpdateIn(InSchema):
    """Modificació d'un usuari per part d'un administrador"""

    password: str | None = Field(default=None, min_length=MIN_PASSWORD, max_length=128)
    role: UserRole | None = None
    active: bool | None = None


class PasswordChangeIn(InSchema):
    """Canvi de la pròpia contrasenya"""

    current_password: str
    new_password: str = Field(min_length=MIN_PASSWORD, max_length=128)

class UserOut(OutSchema):
    """Usuari"""

    id: int
    username: str
    role: UserRole
    active: bool

class WorkgroupBriefOut(OutSchema):
    """Grup simplificat"""

    id: int
    name: str


class UserMeOut(UserOut):
    """El perfil propi, amb els grups als quals es pertany"""

    workgroups: list[WorkgroupBriefOut] = []