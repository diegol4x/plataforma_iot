"""Proves de visibilitat de sensors i lectures, i del filtre de pendents."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.models.catalog import SensorType, Unit
from plataforma_iot.models.device import Device
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.telemetry import Reading, Uplink
from plataforma_iot.models.user import User
from plataforma_iot.models.workgroup import Workgroup

TIME = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def world(session) -> dict:
    """Dos dispositius en grups distints, cadascun amb un sensor i una lectura.

    El primer té a més un sensor pendent de catalogar.
    """
    celsius = Unit(name="Grau Celsius", symbol="Cel")
    session.add(celsius)
    session.flush()

    temperature = SensorType(code="temperature", name="Temperatura", unit_id=celsius.id)
    session.add(temperature)
    session.flush()

    mine = Workgroup(name="El meu grup")
    other = Workgroup(name="Un altre grup")
    session.add_all([mine, other])
    session.flush()

    sensors = {}

    for device_id, group in (("node-meu", mine), ("node-altre", other)):
        device = Device(source="own", device_id=device_id, status=DeviceStatus.ACTIVE)
        session.add(device)
        session.flush()
        group.devices.append(device)

        sensor = Sensor(
            source="own",
            device_id=device_id,
            name="temperature",
            sensor_type_id=temperature.id,
            active=True,
        )
        session.add(sensor)
        session.flush()
        sensors[device_id] = sensor

        uplink = Uplink(time=TIME, received_at=TIME, source="own", device_id=device_id)
        session.add(uplink)
        session.flush()
        session.add(
            Reading(time=TIME, uplink_id=uplink.id, sensor_id=sensor.id, value=21.5)
        )

    pending = Sensor(
        source="own",
        device_id="node-meu",
        name="luminosity",
        sensor_type_id=None,
        active=True,
    )
    session.add(pending)
    session.flush()

    return {"mine": mine, "other": other, "pending": pending}


def _join(session, workgroup: Workgroup) -> None:
    lector = session.scalar(select(User).where(User.username == "lector"))
    workgroup.members.append(lector)
    session.flush()


def test_an_admin_sees_every_sensor(client, admin_auth, world):
    response = client.get("/sensors", headers=admin_auth)

    assert len(response.json()) == 3


def test_a_viewer_without_groups_sees_no_sensors(client, viewer_auth, world):
    assert client.get("/sensors", headers=viewer_auth).json() == []


def test_a_viewer_sees_only_the_sensors_of_their_devices(
    client, viewer_auth, session, world
):
    _join(session, world["mine"])

    response = client.get("/sensors", headers=viewer_auth)

    assert {s["device_id"] for s in response.json()} == {"node-meu"}


def test_a_sensor_of_another_group_gives_404(client, viewer_auth, session, world):
    _join(session, world["mine"])
    alien = session.scalar(select(Sensor).where(Sensor.device_id == "node-altre"))

    assert client.get(f"/sensors/{alien.id}", headers=viewer_auth).status_code == 404


def test_pending_filters_the_uncatalogued_ones(client, admin_auth, world):
    response = client.get("/sensors", params={"pending": True}, headers=admin_auth)

    assert [s["name"] for s in response.json()] == ["luminosity"]
    assert response.json()[0]["unit"] is None


def test_pending_false_leaves_them_out(client, admin_auth, world):
    response = client.get("/sensors", params={"pending": False}, headers=admin_auth)

    assert all(s["name"] == "temperature" for s in response.json())


def test_a_viewer_sees_only_the_readings_of_their_devices(
    client, viewer_auth, session, world
):
    assert client.get("/readings", headers=viewer_auth).json() == []

    _join(session, world["mine"])

    response = client.get("/readings", headers=viewer_auth)
    assert len(response.json()) == 1