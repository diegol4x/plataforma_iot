"""Endpoints d'usuaris."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from plataforma_iot.api.dependencies import current_user, require_admin, delete_or_409
from plataforma_iot.api.schemas import PasswordChangeIn, UserIn, UserOut, UserUpdateIn, UserMeOut
from plataforma_iot.api.security import hash_password, verify_password
from plataforma_iot.db import get_db
from plataforma_iot.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMeOut)
def read_me(user: User = Depends(current_user)) -> User:
    """Torna l'usuari autenticat amb els seus grups"""

    return user

@router.patch("/me", response_model=UserOut)
def change_my_password(
    payload: PasswordChangeIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_db),
) -> User:
    """Canvia la pròpia contrasenya"""

    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=403, detail="La contrasenya actual no és correcta")

    user.password_hash = hash_password(payload.new_password)
    session.commit()
    session.refresh(user)
    return user


@router.get("", response_model=list[UserOut], dependencies=[Depends(require_admin)])
def list_users(session: Session = Depends(get_db)) -> list[User]:
    """Torna tots els usuaris"""

    return list(session.scalars(select(User).order_by(User.username)))


@router.post(
    "", response_model=UserOut, status_code=201, dependencies=[Depends(require_admin)]
)
def create_user(payload: UserIn, session: Session = Depends(get_db)) -> User:
    """Dona d'alta un usuari"""

    existing = session.scalar(select(User).where(User.username == payload.username))
    if existing is not None:
        raise HTTPException(
            status_code=409, detail=f"L'usuari '{payload.username}' ja existix"
        )

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)])
def get_user(user_id: int, session: Session = Depends(get_db)) -> User:
    """Torna un usuari"""

    return _get_or_404(session, user_id)


@router.patch(
    "/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)]
)
def update_user(
    user_id: int,
    payload: UserUpdateIn,
    session: Session = Depends(get_db),
) -> User:
    """Modifica el rol, l'estat o la contrasenya d'un usuari"""

    user = _get_or_404(session, user_id)
    data = payload.model_dump(exclude_unset=True)

    if "password" in data:
        user.password_hash = hash_password(data.pop("password"))

    for field, value in data.items():
        setattr(user, field, value)

    session.commit()
    session.refresh(user)
    return user


def _get_or_404(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuari no trobat")
    return user

@router.delete("/{user_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_user(user_id: int, session: Session = Depends(get_db)) -> None:
    """Esborra un usuari que no siga propietari de cap projecte"""

    user = _get_or_404(session, user_id)
    delete_or_409(session, user, "L'usuari és propietari d'algun projecte")