"""Proves d'autenticació i autorització"""

import pytest

from plataforma_iot.api.security import hash_password
from plataforma_iot.domain.user_role import UserRole
from plataforma_iot.models.user import User

PASSWORD = "contrasenya-de-proves"


@pytest.fixture
def admin(session) -> User:
    user = User(
        username="admin",
        password_hash=hash_password(PASSWORD),
        role=UserRole.ADMIN,
    )
    session.add(user)
    session.flush()
    return user


@pytest.fixture
def viewer(session) -> User:
    user = User(
        username="lector",
        password_hash=hash_password(PASSWORD),
        role=UserRole.VIEWER,
    )
    session.add(user)
    session.flush()
    return user


def _token(client, username: str) -> str:
    response = client.post(
        "/auth/token", data={"username": username, "password": PASSWORD}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_login_returns_a_token(client, admin):
    response = client.post(
        "/auth/token", data={"username": "admin", "password": PASSWORD}
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_rejects_a_wrong_password(client, admin):
    response = client.post(
        "/auth/token", data={"username": "admin", "password": "una-altra"}
    )

    assert response.status_code == 401


def test_unknown_user_fails_like_a_wrong_password(client, admin):
    wrong_password = client.post(
        "/auth/token", data={"username": "admin", "password": "una-altra"}
    )
    unknown_user = client.post(
        "/auth/token", data={"username": "ningu", "password": PASSWORD}
    )

    assert unknown_user.status_code == wrong_password.status_code
    assert unknown_user.json() == wrong_password.json()


def test_rejects_an_inactive_user(client, session, admin):
    admin.active = False
    session.flush()

    response = client.post(
        "/auth/token", data={"username": "admin", "password": PASSWORD}
    )

    assert response.status_code == 403


def test_requires_a_token(client):
    assert client.get("/devices").status_code == 401


def test_rejects_an_invalid_token(client):
    response = client.get("/devices", headers=_auth("aixo-no-es-un-token"))

    assert response.status_code == 401


def test_a_viewer_can_read(client, viewer):
    response = client.get("/devices", headers=_auth(_token(client, "lector")))

    assert response.status_code == 200


def test_a_viewer_cannot_write(client, viewer, project):
    response = client.post(
        "/spaces",
        json={"name": "Saló", "type": "space", "project_id": project.id},
        headers=_auth(_token(client, "lector")),
    )

    assert response.status_code == 403


def test_an_admin_can_write(client, admin, project):
    response = client.post(
        "/spaces",
        json={"name": "Saló", "type": "space", "project_id": project.id},
        headers=_auth(_token(client, "admin")),
    )

    assert response.status_code == 201

def test_a_viewer_cannot_see_discards(client, viewer_auth):
    """Els descarts guarden el payload cru: sols administració."""
    assert client.get("/discards", headers=viewer_auth).status_code == 403

def test_a_viewer_cannot_see_uplinks(client, viewer_auth):
    """Els uplinks mostren metadades de transport: sols administració."""
    assert client.get("/uplinks", headers=viewer_auth).status_code == 403