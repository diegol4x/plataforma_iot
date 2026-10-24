"""Dependències d'autenticació i autorització"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from plataforma_iot.api.security import decode_access_token
from plataforma_iot.db import get_db
from plataforma_iot.domain.user_role import UserRole
from plataforma_iot.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="token invàlid o caducat",
    headers={"WWW-Authenticate": "Bearer"},
)

def current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db),
) -> User:
    """Verifica el token i torna l'usuari que el presenta"""
    
    try:
        payload = decode_access_token(token)
        username = payload["sub"]
    except (jwt.PyJWTError, KeyError) as exc:
        raise _UNAUTHORIZED from exc

    user = session.scalar(select(User).where(User.username == username))

    if user is None or not user.active:
        raise _UNAUTHORIZED

    return user

def require_admin(user: User = Depends(current_user)) -> User:
    """Exigix rol d'administrador"""
    if user.role is not UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="cal rol d'administrador",
        )
    return user

def delete_or_409(session: Session, item, detail: str) -> None:
    """Esborra un recurs, o torna 409 si encara té dependències"""
    
    session.delete(item)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc