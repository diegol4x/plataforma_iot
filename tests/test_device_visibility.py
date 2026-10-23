"""Proves de visibilitat de dispositius segons els grups de l'usuari."""

import pytest

from sqlalchemy import select

from plataforma_iot.models.user import User

from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.models.device import Device
from plataforma_iot.models.workgroup import Workgroup


@pytest.fixture
def devices(session) -> dict:
    """Dos dispositius en grups distints i un tercer sense grup."""
    mine = Workgroup(name="El meu grup")
    other = Workgroup(name="Un altre grup")
    session.add_all([mine, other])
    session.flush()

    for device_id in ("node-meu", "node-altre", "node-orfe"):
        session.add(
            Device(source="own", device_id=device_id, status=DeviceStatus.ACTIVE)
        )
    session.flush()

    mine.devices.append(session.get(Device, ("own", "node-meu")))
    other.devices.append(session.get(Device, ("own", "node-altre")))
    session.flush()

    return {"mine": mine, "other": other}


def test_an_admin_sees_every_device(client, admin_auth, devices):
    response = client.get("/devices", headers=admin_auth)

    assert {d["device_id"] for d in response.json()} == {
        "node-meu",
        "node-altre",
        "node-orfe",
    }


def test_a_viewer_without_groups_sees_nothing(client, viewer_auth, devices):
    response = client.get("/devices", headers=viewer_auth)

    assert response.json() == []


def test_a_viewer_sees_only_the_devices_of_their_groups(
    client, viewer_auth, session, devices
):
    lector = session.scalar(select(User).where(User.username == "lector"))
    devices["mine"].members.append(lector)
    session.flush()

    response = client.get("/devices", headers=viewer_auth)

    assert [d["device_id"] for d in response.json()] == ["node-meu"]


def test_an_unassigned_device_is_invisible_to_a_viewer(
    client, viewer_auth, session, devices
):
    """Un dispositiu acabat de descobrir encara no l'ha reclamat ningú."""
    lector = session.scalar(select(User).where(User.username == "lector"))
    devices["mine"].members.append(lector)
    session.flush()

    response = client.get("/devices/own/node-orfe", headers=viewer_auth)

    assert response.status_code == 404


def test_a_device_of_another_group_gives_404_not_403(
    client, viewer_auth, session, devices
):
    """404 i no 403: un 403 confirmaria que eixe dispositiu existix."""
    lector = session.scalar(select(User).where(User.username == "lector"))
    devices["mine"].members.append(lector)
    session.flush()

    response = client.get("/devices/own/node-altre", headers=viewer_auth)

    assert response.status_code == 404