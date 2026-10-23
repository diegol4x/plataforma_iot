"""Proves del provisionament de dispositius"""

import pytest

from plataforma_iot.api.security import hash_password
from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.domain.user_role import UserRole
from plataforma_iot.models.device import Device
from plataforma_iot.models.space import Space
from plataforma_iot.models.user import User

PASSWORD = "contrasenya-de-proves"
PATH = "/devices/own/node-00"


@pytest.fixture
def auth(client, session) -> dict:
    """Header d'autenticació d'un administrador"""
    session.add(
        User(
            username="admin",
            password_hash=hash_password(PASSWORD),
            role=UserRole.ADMIN,
        )
    )
    session.flush()

    response = client.post(
        "/auth/token", data={"username": "admin", "password": PASSWORD}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def device(session) -> Device:
    """Dispositiu acabat de descobrir"""
    item = Device(
        source="own",
        device_id="node-00",
        type="node",
        status=DeviceStatus.UNPROVISIONED,
    )
    session.add(item)
    session.flush()
    return item


@pytest.fixture
def space(session, project) -> Space:
    item = Space(name="Saló", type="space", project_id=project.id)
    session.add(item)
    session.flush()
    return item


def test_provisioning_activates_the_device(client, auth, device):
    response = client.patch(PATH, json={"name": "Node de proves"}, headers=auth)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "active"
    assert body["name"] == "Node de proves"


def test_provisioning_can_assign_a_space(client, auth, device, space):
    response = client.patch(
        PATH, json={"name": "Node", "space_id": space.id}, headers=auth
    )

    assert response.json()["space_id"] == space.id


def test_rejects_an_unknown_space(client, auth, device):
    response = client.patch(PATH, json={"name": "Node", "space_id": 9999}, headers=auth)

    assert response.status_code == 422


def test_an_unprovisioned_device_cannot_go_to_another_state(client, auth, device):
    response = client.patch(
        PATH, json={"name": "Node", "status": "silent"}, headers=auth
    )

    assert response.status_code == 409


def test_a_provisioned_device_can_be_renamed(client, auth, session, device):
    device.status = DeviceStatus.ACTIVE
    device.name = "Nom antic"
    session.flush()

    response = client.patch(PATH, json={"name": "Nom nou"}, headers=auth)

    assert response.status_code == 200
    assert response.json()["name"] == "Nom nou"
    assert response.json()["status"] == "active"


def test_the_state_of_a_provisioned_device_cannot_be_set(client, auth, session, device):
    """Els estats operatius no es posen a mà, ni el mateix que té ara"""
    device.status = DeviceStatus.ACTIVE
    session.flush()

    response = client.patch(
        PATH, json={"name": "Node", "status": "active"}, headers=auth
    )

    assert response.status_code == 409


def test_a_silent_device_cannot_be_reactivated_by_hand(client, auth, session, device):
    device.status = DeviceStatus.SILENT
    session.flush()

    response = client.patch(
        PATH, json={"name": "Node", "status": "active"}, headers=auth
    )

    assert response.status_code == 409


def test_an_omitted_space_is_not_cleared(client, auth, session, device, space):
    """Un PATCH modifica el que se li envia, no el que s'omet"""
    device.status = DeviceStatus.ACTIVE
    device.space_id = space.id
    session.flush()

    response = client.patch(PATH, json={"name": "Nom nou"}, headers=auth)

    assert response.json()["space_id"] == space.id


def test_a_null_space_is_cleared(client, auth, session, device, space):
    device.status = DeviceStatus.ACTIVE
    device.space_id = space.id
    session.flush()

    response = client.patch(
        PATH, json={"name": "Node", "space_id": None}, headers=auth
    )

    assert response.json()["space_id"] is None


def test_rejects_an_unknown_field(client, auth, device):
    response = client.patch(
        PATH, json={"name": "Node", "last_seen": "2026-01-01T00:00:00Z"}, headers=auth
    )

    assert response.status_code == 422


def test_rejects_an_unknown_device(client, auth):
    response = client.patch("/devices/own/no-existix", json={"name": "X"}, headers=auth)

    assert response.status_code == 404