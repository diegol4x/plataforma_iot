"""Crea un usuari de la plataforma."""

import argparse
import os

from sqlalchemy import select

from plataforma_iot.api.security import hash_password
from plataforma_iot.db import get_session
from plataforma_iot.domain.user_role import UserRole
from plataforma_iot.models.user import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea un usuari")
    parser.add_argument("username")
    parser.add_argument("--role", choices=[role.value for role in UserRole], default="viewer")
    args = parser.parse_args()

    password = os.environ.get("NEW_USER_PASSWORD")
    if not password:
        raise SystemExit("Cal definir NEW_USER_PASSWORD en l'entorn")

    with get_session() as session:
        if session.scalar(select(User).where(User.username == args.username)) is not None:
            raise SystemExit(f"L'usuari '{args.username}' ja existix")

        session.add(
            User(
                username=args.username,
                password_hash=hash_password(password),
                role=UserRole(args.role),
            )
        )
        session.commit()

    print(f"Usuari '{args.username}' creat amb rol {args.role}")


if __name__ == "__main__":
    main()