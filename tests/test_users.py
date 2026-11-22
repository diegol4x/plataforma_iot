"""Proves de la gestió d'usuaris."""

import pytest
from sqlalchemy import select

from plataforma_iot.api.security import verify_password
from plataforma_iot.domain.user_role import UserRole
from plataforma_iot.models.user import User
from plataforma_iot.models.workgroup import Workgroup
from plataforma_iot.models.project import Project


TEST_PASSWORD = "contrasenya-de-proves"
NEW_PASSWORD = "una-contrasenya-nova"


def _find(session, username: str) -> User:
    return session.scalar(select(User).where(User.username == username))


def test_me_returns_the_authenticated_user(client, viewer_auth):
    response = client.get("/users/me", headers=viewer_auth)

    assert response.status_code == 200
    assert response.json()["username"] == "lector"


def test_me_is_not_read_as_an_id(client, viewer_auth):
    """La ruta /me va declarada abans que /{user_id}, o es llegiria com un enter."""
    assert client.get("/users/me", headers=viewer_auth).status_code == 200


def test_a_viewer_cannot_list_users(client, viewer_auth):
    assert client.get("/users", headers=viewer_auth).status_code == 403


def test_an_admin_creates_a_user(client, admin_auth, session):
    response = client.post(
        "/users",
        json={"username": "nou", "password": TEST_PASSWORD},
        headers=admin_auth,
    )

    assert response.status_code == 201
    assert response.json()["role"] == "viewer"
    assert verify_password(TEST_PASSWORD, _find(session, "nou").password_hash)


def test_the_username_is_unique(client, admin_auth):
    body = {"username": "nou", "password": TEST_PASSWORD}
    client.post("/users", json=body, headers=admin_auth)

    assert client.post("/users", json=body, headers=admin_auth).status_code == 409


def test_a_short_password_is_rejected(client, admin_auth):
    response = client.post(
        "/users", json={"username": "nou", "password": "curta"}, headers=admin_auth
    )

    assert response.status_code == 422


def test_changing_my_password_needs_the_current_one(client, viewer_auth):
    response = client.patch(
        "/users/me",
        json={"current_password": "la-que-no-es", "new_password": NEW_PASSWORD},
        headers=viewer_auth,
    )

    assert response.status_code == 403


def test_the_new_password_works(client, viewer_auth, session):
    client.patch(
        "/users/me",
        json={"current_password": TEST_PASSWORD, "new_password": NEW_PASSWORD},
        headers=viewer_auth,
    )

    response = client.post(
        "/auth/token", data={"username": "lector", "password": NEW_PASSWORD}
    )
    assert response.status_code == 200


def test_a_viewer_cannot_promote_themselves(client, viewer_auth, session):
    """El rol no es toca des de /me: és una operació d'administració."""
    lector = _find(session, "lector")

    response = client.patch(
        f"/users/{lector.id}", json={"role": "admin"}, headers=viewer_auth
    )

    assert response.status_code == 403


def test_an_admin_deactivates_a_user(client, admin_auth, viewer_auth, session):
    """Desactivar té efecte immediat: el token deixa de valdre sense esperar."""
    lector = _find(session, "lector")

    client.patch(f"/users/{lector.id}", json={"active": False}, headers=admin_auth)

    assert client.get("/users/me", headers=viewer_auth).status_code == 401


def test_rejects_an_unknown_user(client, admin_auth):
    assert client.get("/users/9999", headers=admin_auth).status_code == 404


def test_a_user_who_owns_projects_cannot_be_deleted(client, admin_auth, session):
    created = client.post(
        "/users",
        json={"username": "propietari", "password": TEST_PASSWORD},
        headers=admin_auth,
    ).json()

    workgroup = Workgroup(name="Grup")
    session.add(workgroup)
    session.flush()
    session.add(Project(name="Seu", workgroup_id=workgroup.id, owner_id=created["id"]))
    session.flush()

    assert client.delete(f"/users/{created['id']}", headers=admin_auth).status_code == 409

def test_a_user_without_projects_can_be_deleted(client, admin_auth):
    created = client.post(
        "/users",
        json={"username": "efimer", "password": TEST_PASSWORD},
        headers=admin_auth,
    ).json()

    assert client.delete(f"/users/{created['id']}", headers=admin_auth).status_code == 204

def test_me_includes_the_users_workgroups(client, viewer_auth, session):
    """Un viewer necessita saber-ho per a crear projectes, i no pot llistar grups."""
    lector = _find(session, "lector")
    workgroup = Workgroup(name="Laboratori")
    workgroup.members.append(lector)
    session.add(workgroup)
    session.flush()

    response = client.get("/users/me", headers=viewer_auth)

    assert [g["name"] for g in response.json()["workgroups"]] == ["Laboratori"]