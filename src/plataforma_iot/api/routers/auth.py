"""Endpoint d'autenticació"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from plataforma_iot.api.schemas import TokenOut
from plataforma_iot.api.security import create_access_token, verify_password
from plataforma_iot.db import get_db
from plataforma_iot.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/token", response_model=TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_db),
) -> TokenOut:
    """Valida les credencials i emet un token d'accés"""

    user = session.scalar(select(User).where(User.username == form.username))

    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="credencials invàlides",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="usuari desactivat")

    return TokenOut(access_token=create_access_token(user.username, user.role))