"""Proves de projectes: creació dins del grup i propietat individual."""

import pytest
from sqlalchemy import select

from plataforma_iot.api.security import hash_password
from plataforma_iot.domain.user_role import UserRole
from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.models.project import Project
from plataforma_iot.models.user import User
from plataforma_iot.models.workgroup import Workgroup
from plataforma_iot.models.device import Device
from plataforma_iot.models.space import Space

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

def test_a_device_can_be_in_equivalent_spaces_of_two_projects(
    client, admin_auth, session, workgroup
):
    """El mateix saló físic, representat en dos projectes: un sol sensor als dos."""
    device = Device(source="own", device_id="node-00", status=DeviceStatus.ACTIVE)
    session.add(device)
    session.flush()

    owner = session.scalar(select(User).where(User.username == "admin"))
    first = Project(name="Estudi A", workgroup_id=workgroup.id, owner_id=owner.id)
    second = Project(name="Estudi B", workgroup_id=workgroup.id, owner_id=owner.id)
    session.add_all([first, second])
    session.flush()

    salon_a = Space(name="Saló", type="space", project_id=first.id)
    salon_b = Space(name="Sala d'estar", type="space", project_id=second.id)
    session.add_all([salon_a, salon_b])
    session.flush()

    client.put(f"/spaces/{salon_a.id}/devices/own/node-00", headers=admin_auth)
    client.put(f"/spaces/{salon_b.id}/devices/own/node-00", headers=admin_auth)

    in_a = client.get(f"/spaces/{salon_a.id}/devices", headers=admin_auth)
    in_b = client.get(f"/spaces/{salon_b.id}/devices", headers=admin_auth)
    assert len(in_a.json()) == 1
    assert len(in_b.json()) == 1


def test_moving_within_a_project_replaces_the_previous_space(
    client, admin_auth, session, workgroup
):
    """Dins d'un projecte un dispositiu sols està en un espai: el PUT el mou."""
    device = Device(source="own", device_id="node-00", status=DeviceStatus.ACTIVE)
    session.add(device)
    session.flush()

    owner = session.scalar(select(User).where(User.username == "admin"))
    project = Project(name="Estudi", workgroup_id=workgroup.id, owner_id=owner.id)
    session.add(project)
    session.flush()

    kitchen = Space(name="Cuina", type="space", project_id=project.id)
    bedroom = Space(name="Habitació", type="space", project_id=project.id)
    session.add_all([kitchen, bedroom])
    session.flush()

    client.put(f"/spaces/{kitchen.id}/devices/own/node-00", headers=admin_auth)
    client.put(f"/spaces/{bedroom.id}/devices/own/node-00", headers=admin_auth)

    assert client.get(f"/spaces/{kitchen.id}/devices", headers=admin_auth).json() == []
    assert len(client.get(f"/spaces/{bedroom.id}/devices", headers=admin_auth).json()) == 1


def test_a_project_with_spaces_cannot_be_deleted(client, admin_auth, session, workgroup):
    owner = session.scalar(select(User).where(User.username == "admin"))
    project = Project(name="Estudi", workgroup_id=workgroup.id, owner_id=owner.id)
    session.add(project)
    session.flush()
    session.add(Space(name="Sala", type="space", project_id=project.id))
    session.flush()

    response = client.delete(f"/projects/{project.id}", headers=admin_auth)

    assert response.status_code == 409


def test_an_empty_project_can_be_deleted(client, admin_auth, session, workgroup):
    owner = session.scalar(select(User).where(User.username == "admin"))
    project = Project(name="Buit", workgroup_id=workgroup.id, owner_id=owner.id)
    session.add(project)
    session.flush()

    assert client.delete(f"/projects/{project.id}", headers=admin_auth).status_code == 204


def test_another_member_cannot_delete_it(client, session, workgroup):
    owner_auth = _auth(client, session, "propietari", workgroup)
    created = client.post(
        "/projects", json={"name": "Pilot", "workgroup_id": workgroup.id}, headers=owner_auth
    ).json()

    other_auth = _auth(client, session, "company", workgroup)

    assert client.delete(f"/projects/{created['id']}", headers=other_auth).status_code == 403