"""Configuració comuna de les proves."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from collections.abc import Generator

from plataforma_iot.api.app import app
from plataforma_iot.db import get_db
from plataforma_iot.models.base import Base

ADMIN_URL = os.environ.get(
    "TEST_ADMIN_URL", "postgresql+psycopg://appuser:appuser@localhost:5432/postgres"
)
TEST_DB = "iot_monitoring_test"
TEST_URL = ADMIN_URL.rsplit("/", 1)[0] + f"/{TEST_DB}"


@pytest.fixture(scope="session")
def engine():
    """Crea una base de dades de proves neta i la destruïx en acabar."""
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")

    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB}"))
        conn.execute(text(f"CREATE DATABASE {TEST_DB}"))

    test_engine = create_engine(TEST_URL)
    Base.metadata.create_all(test_engine)

    yield test_engine

    test_engine.dispose()
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB}"))
    admin.dispose()


@pytest.fixture
def session(engine) -> Generator[Session]:
    """Sessió aïllada: cada prova treballa sobre una transacció que es desfà."""
    connection = engine.connect()
    transaction = connection.begin()
    factory = sessionmaker(bind=connection)
    db = factory()

    yield db

    db.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(session) -> Generator[TestClient]:
    """Client HTTP amb la sessió de proves injectada."""
    app.dependency_overrides[get_db] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()