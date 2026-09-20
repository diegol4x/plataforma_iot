"""Connexió a la base de dades i utilitats de sessió."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from plataforma_iot.config import settings

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_session() -> Session:
    """Torna una nova sessió de base de dades.

    Qui la demana s'encarrega de tancar-la, normalment amb `with`.
    """
    return SessionLocal()


def get_db() -> Generator[Session, None, None]:
    """Proveïx una sessió per petició i la tanca en acabar (FastAPI).

    L'esquema el gestiona Alembic: ací no es crea cap taula.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()