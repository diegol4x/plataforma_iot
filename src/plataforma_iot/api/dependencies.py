"""Dependències d'autenticació i autorització"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from plataforma_iot.api.security import decode_access_token
from plataforma_iot.domain.user_role import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="token invàlid o caducat",
    headers={"WWW-Authenticate": "Bearer"},
)

def current_role(token: str = Depends(oauth2_scheme)) -> UserRole:
    """Verifica el token i torna el rol de qui el presenta."""
    try:
        payload = decode_access_token(token)
        return UserRole(payload["role"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise _UNAUTHORIZED from exc


def require_admin(role: UserRole = Depends(current_role)) -> UserRole:
    """Exigix rol d'administrador."""
    if role is not UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="cal rol d'administrador",
        )
    return role