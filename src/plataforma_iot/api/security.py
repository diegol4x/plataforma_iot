"""Seguretat:
    - Hash de contrasenyes 
    - Emissió i verificació de tokens JWT.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from plataforma_iot.config import settings
from plataforma_iot.domain.user_role import UserRole

_MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    """Calcula el hash de contrasenyes"""
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Comprova contrasenya contra el seu hash"""
    return bcrypt.checkpw(_encode(password), password_hash.encode())


def _encode(password: str) -> bytes:
    """Codifica la contrasenya al límit de bytes que admet bcrypt"""
    return password.encode("utf-8")[:_MAX_PASSWORD_BYTES]


def create_access_token(username: str, role: UserRole) -> str:
    """Emet un token firmat per a un usuari."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "role": role.value,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Verifica la firma i la caducitat del token i torna el seu contingut"""

    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
