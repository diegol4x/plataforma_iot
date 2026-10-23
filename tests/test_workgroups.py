"""Proves dels grups de treball i la seua composició."""

import pytest

from sqlalchemy import select

from plataforma_iot.api.security import hash_password
from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.domain.user_role import UserRole
from plataforma_iot.models.device import Device
from plataforma_iot.models.user import User
from plataforma_iot.models.workgroup import Workgroup

TEST_PASSWORD = "contrasenya-de-proves"

@pytest.fixture
def workgroup(session) -> Workgroup:
    item = Workgroup(name="Laboratori")
    session.add(item)
    session.flush()
    return item


@pytest.fixture
def member(session) -> User:
    """Un usuari qualsevol, per a afegir-lo i traure'l del grup."""
    item = User(
        username="membre",
        password_hash=hash_password(TEST_PASSWORD),
        role=UserRole.VIEWER,
    )
    session.add(item)
    session.flush()
    return item


@pytest.fixture
def device(session) -> Device:
    item = Device(source="own", device_id="node-00", status=DeviceStatus.ACTIVE)
    session.add(item)
    session.flush()
    return item


def test_a_viewer_cannot_manage_workgroups(client, viewer_auth):
    assert client.get("/workgroups", headers=viewer_auth).status_code == 403


def test_adds_a_member(client, admin_auth, workgroup, member):
    response = client.put(
        f"/workgroups/{workgroup.id}/members/{member.id}", headers=admin_auth
    )

    assert response.status_code == 204

    members = client.get(f"/workgroups/{workgroup.id}/members", headers=admin_auth)
    assert [u["username"] for u in members.json()] == ["membre"]


def test_adding_a_member_twice_changes_nothing(client, admin_auth, workgroup, member):
    """Un PUT és idempotent: el resultat és el mateix estat, no un error."""
    path = f"/workgroups/{workgroup.id}/members/{member.id}"
    client.put(path, headers=admin_auth)

    assert client.put(path, headers=admin_auth).status_code == 204

    members = client.get(f"/workgroups/{workgroup.id}/members", headers=admin_auth)
    assert len(members.json()) == 1


def test_removes_a_member(client, admin_auth, workgroup, member):
    path = f"/workgroups/{workgroup.id}/members/{member.id}"
    client.put(path, headers=admin_auth)

    assert client.delete(path, headers=admin_auth).status_code == 204

    members = client.get(f"/workgroups/{workgroup.id}/members", headers=admin_auth)
    assert members.json() == []


def test_removing_someone_who_was_not_a_member_is_not_an_error(
    client, admin_auth, workgroup, member
):
    """L'estat final és el demanat, així que no hi ha res a reportar."""
    response = client.delete(
        f"/workgroups/{workgroup.id}/members/{member.id}", headers=admin_auth
    )

    assert response.status_code == 204


def test_rejects_an_unknown_user(client, admin_auth, workgroup):
    response = client.put(f"/workgroups/{workgroup.id}/members/9999", headers=admin_auth)

    assert response.status_code == 404


def test_assigns_a_device(client, admin_auth, workgroup, device):
    response = client.put(
        f"/workgroups/{workgroup.id}/devices/own/node-00", headers=admin_auth
    )

    assert response.status_code == 204

    devices = client.get(f"/workgroups/{workgroup.id}/devices", headers=admin_auth)
    assert [d["device_id"] for d in devices.json()] == ["node-00"]


def test_a_device_can_be_in_several_groups(client, admin_auth, session, workgroup, device):
    other = Workgroup(name="Un altre")
    session.add(other)
    session.flush()

    client.put(f"/workgroups/{workgroup.id}/devices/own/node-00", headers=admin_auth)
    client.put(f"/workgroups/{other.id}/devices/own/node-00", headers=admin_auth)

    first = client.get(f"/workgroups/{workgroup.id}/devices", headers=admin_auth)
    second = client.get(f"/workgroups/{other.id}/devices", headers=admin_auth)
    assert len(first.json()) == 1
    assert len(second.json()) == 1


def test_removing_a_device_does_not_touch_other_groups(
    client, admin_auth, session, workgroup, device
):
    other = Workgroup(name="Un altre")
    session.add(other)
    session.flush()

    client.put(f"/workgroups/{workgroup.id}/devices/own/node-00", headers=admin_auth)
    client.put(f"/workgroups/{other.id}/devices/own/node-00", headers=admin_auth)

    client.delete(f"/workgroups/{workgroup.id}/devices/own/node-00", headers=admin_auth)

    still_there = client.get(f"/workgroups/{other.id}/devices", headers=admin_auth)
    assert len(still_there.json()) == 1


def test_assigning_a_device_makes_it_visible_to_the_members(
    client, admin_auth, viewer_auth, session, workgroup, device
):
    """La peça que uneix tot: la pertinença al grup decidix què veu un viewer."""
    assert client.get("/devices", headers=viewer_auth).json() == []

    lector = session.scalar(select(User).where(User.username == "lector"))
    client.put(f"/workgroups/{workgroup.id}/members/{lector.id}", headers=admin_auth)
    client.put(f"/workgroups/{workgroup.id}/devices/own/node-00", headers=admin_auth)

    response = client.get("/devices", headers=viewer_auth)
    assert [d["device_id"] for d in response.json()] == ["node-00"]