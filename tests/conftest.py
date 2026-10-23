"""Configuració comuna de les proves."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from plataforma_iot.api.app import app
from plataforma_iot.api.security import hash_password
from plataforma_iot.db import get_db
from plataforma_iot.domain.user_role import UserRole
from plataforma_iot.models.base import Base
from plataforma_iot.models.user import User
from plataforma_iot.models.project import Project
from plataforma_iot.models.workgroup import Workgroup


ADMIN_URL = os.environ.get(
    "TEST_ADMIN_URL", "postgresql+psycopg://appuser:appuser@localhost:5432/postgres"
)
TEST_DB = "iot_monitoring_test"
TEST_URL = ADMIN_URL.rsplit("/", 1)[0] + f"/{TEST_DB}"
TEST_PASSWORD = "contrasenya-de-proves"


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


def _auth_header(client: TestClient, session: Session, username: str, role: UserRole) -> dict:
    """Crea un usuari amb el rol indicat i torna la seua capçalera d'autenticació."""
    session.add(
        User(
            username=username,
            password_hash=hash_password(TEST_PASSWORD),
            role=role,
        )
    )
    session.flush()

    response = client.post(
        "/auth/token", data={"username": username, "password": TEST_PASSWORD}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def admin_auth(client, session) -> dict:
    """Capçalera d'autenticació d'un administrador."""
    return _auth_header(client, session, "admin", UserRole.ADMIN)


@pytest.fixture
def viewer_auth(client, session) -> dict:
    """Capçalera d'autenticació d'un lector."""
    return _auth_header(client, session, "lector", UserRole.VIEWER)

@pytest.fixture
def project(session) -> Project:
    """Un projecte amb el seu grup i propietari, per a penjar-hi espais."""
    workgroup = Workgroup(name="Grup de proves")
    owner = User(
        username="propietari",
        password_hash=hash_password(TEST_PASSWORD),
        role=UserRole.VIEWER,
    )
    session.add_all([workgroup, owner])
    session.flush()

    item = Project(name="Projecte de proves", workgroup_id=workgroup.id, owner_id=owner.id)
    session.add(item)
    session.flush()
    return item