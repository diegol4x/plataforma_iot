"""Proves de projectes: creació dins del grup i propietat individual."""

import pytest
from sqlalchemy import select

from plataforma_iot.api.security import hash_password
from plataforma_iot.domain.user_role import UserRole
from plataforma_iot.models.project import Project
from plataforma_iot.models.user import User
from plataforma_iot.models.workgroup import Workgroup

TEST_PASSWORD = "contrasenya-de-proves"


def _auth(client, session, username: str, workgroup: Workgroup | None = None) -> dict:
    """Crea un viewer, opcionalment dins d'un grup, i torna la seua capçalera."""
    user = User(
        username=username,
        password_hash=hash_password(TEST_PASSWORD),
        role=UserRole.VIEWER,
    )
    session.add(user)
    session.flush()

    if workgroup is not None:
        workgroup.members.append(user)
        session.flush()

    response = client.post(
        "/auth/token", data={"username": username, "password": TEST_PASSWORD}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def workgroup(session) -> Workgroup:
    item = Workgroup(name="Laboratori")
    session.add(item)
    session.flush()
    return item


def test_a_viewer_creates_a_project_in_their_group(client, session, workgroup):
    auth = _auth(client, session, "membre", workgroup)

    response = client.post(
        "/projects",
        json={"name": "Pilot", "workgroup_id": workgroup.id},
        headers=auth,
    )

    assert response.status_code == 201
    created = session.scalar(select(User).where(User.username == "membre"))
    assert response.json()["owner_id"] == created.id


def test_a_viewer_cannot_create_in_a_group_they_are_not_in(client, session, workgroup):
    auth = _auth(client, session, "forani")

    response = client.post(
        "/projects",
        json={"name": "Pilot", "workgroup_id": workgroup.id},
        headers=auth,
    )

    assert response.status_code == 403


def test_the_name_is_unique_within_the_group(client, session, workgroup):
    auth = _auth(client, session, "membre", workgroup)
    body = {"name": "Pilot", "workgroup_id": workgroup.id}
    client.post("/projects", json=body, headers=auth)

    assert client.post("/projects", json=body, headers=auth).status_code == 409


def test_the_same_name_is_fine_in_another_group(client, session, workgroup):
    other = Workgroup(name="Un altre")
    session.add(other)
    session.flush()

    auth = _auth(client, session, "membre", workgroup)
    other.members.append(session.scalar(select(User).where(User.username == "membre")))
    session.flush()

    client.post("/projects", json={"name": "Pilot", "workgroup_id": workgroup.id}, headers=auth)
    response = client.post(
        "/projects", json={"name": "Pilot", "workgroup_id": other.id}, headers=auth
    )

    assert response.status_code == 201


def test_the_owner_can_edit_it(client, session, workgroup):
    auth = _auth(client, session, "membre", workgroup)
    created = client.post(
        "/projects", json={"name": "Pilot", "workgroup_id": workgroup.id}, headers=auth
    ).json()

    response = client.patch(
        f"/projects/{created['id']}", json={"name": "Pilot 2"}, headers=auth
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Pilot 2"


def test_another_member_sees_it_but_cannot_edit_it(client, session, workgroup):
    """La diferència entre vore i posseir: 403, no 404, perquè ja sap que existix."""
    owner_auth = _auth(client, session, "propietari", workgroup)
    created = client.post(
        "/projects", json={"name": "Pilot", "workgroup_id": workgroup.id}, headers=owner_auth
    ).json()

    other_auth = _auth(client, session, "company", workgroup)

    assert client.get(f"/projects/{created['id']}", headers=other_auth).status_code == 200
    assert (
        client.patch(
            f"/projects/{created['id']}", json={"name": "Meu"}, headers=other_auth
        ).status_code
        == 403
    )


def test_someone_outside_the_group_gets_a_404(client, session, workgroup, admin_auth):
    """Qui no el pot vore no ha de saber que existix: 404, no 403."""
    project = Project(
        name="Pilot",
        workgroup_id=workgroup.id,
        owner_id=session.scalar(select(User).where(User.username == "admin")).id,
    )
    session.add(project)
    session.flush()

    auth = _auth(client, session, "forani")

    assert client.get(f"/projects/{project.id}", headers=auth).status_code == 404


def test_an_admin_can_edit_any_project(client, session, workgroup, admin_auth):
    owner_auth = _auth(client, session, "propietari", workgroup)
    created = client.post(
        "/projects", json={"name": "Pilot", "workgroup_id": workgroup.id}, headers=owner_auth
    ).json()

    response = client.patch(
        f"/projects/{created['id']}", json={"name": "Intervingut"}, headers=admin_auth
    )

    assert response.status_code == 200

def test_the_owner_can_create_spaces_in_their_project(client, session, workgroup):
    auth = _auth(client, session, "membre", workgroup)
    project = client.post(
        "/projects", json={"name": "Pilot", "workgroup_id": workgroup.id}, headers=auth
    ).json()

    response = client.post(
        "/spaces",
        json={"name": "Sala", "type": "space", "project_id": project["id"]},
        headers=auth,
    )

    assert response.status_code == 201


def test_another_member_cannot_create_spaces_there(client, session, workgroup):
    owner_auth = _auth(client, session, "propietari", workgroup)
    project = client.post(
        "/projects", json={"name": "Pilot", "workgroup_id": workgroup.id}, headers=owner_auth
    ).json()

    other_auth = _auth(client, session, "company", workgroup)

    response = client.post(
        "/spaces",
        json={"name": "Sala", "type": "space", "project_id": project["id"]},
        headers=other_auth,
    )

    assert response.status_code == 403