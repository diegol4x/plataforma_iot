"""Conexión a la base de datos y utilidades de sesión."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from plataforma_iot.config import settings
from plataforma_iot.models import Base

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Crea las tablas si no existen todavía."""
    Base.metadata.create_all(engine)


def get_session() -> Session:
    """Devuelve una nueva sesión de base de datos."""
    return SessionLocal()