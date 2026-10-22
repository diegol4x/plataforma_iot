"""Proves de les agregacions per espai"""

from datetime import datetime, timedelta, timezone

import pytest

from plataforma_iot.api.security import hash_password
from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.domain.user_role import UserRole
from plataforma_iot.models.catalog import SensorType, Unit
from plataforma_iot.models.device import Device
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.space import Space
from plataforma_iot.models.telemetry import Reading, Uplink
from plataforma_iot.models.user import User

PASSWORD = "contrasenya-de-proves"
START = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def auth(client, session) -> dict:
    """Header d'autenticació d'un lector"""
    session.add(
        User(
            username="lector",
            password_hash=hash_password(PASSWORD),
            role=UserRole.VIEWER,
        )
    )
    session.flush()

    response = client.post(
        "/auth/token", data={"username": "lector", "password": PASSWORD}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def world(session) -> dict:
    """Edifici > planta > saló, amb un node que mesura temperatura"""
    
    building = Space(name="Edifici", type="building")
    session.add(building)
    session.flush()

    floor = Space(name="Planta", type="storey", parent_id=building.id)
    session.add(floor)
    session.flush()

    room = Space(name="Saló", type="space", parent_id=floor.id)
    session.add(room)
    session.flush()

    celsius = Unit(name="Grau Celsius", symbol="Cel")
    session.add(celsius)
    session.flush()

    temperature = SensorType(code="temperature", name="Temperatura", unit_id=celsius.id)
    session.add(temperature)
    session.flush()

    device = Device(
        source="own",
        device_id="node-00",
        type="node",
        status=DeviceStatus.ACTIVE,
        space_id=room.id,
    )
    session.add(device)
    session.flush()

    sensor = Sensor(
        source="own",
        device_id="node-00",
        name="temperature",
        sensor_type_id=temperature.id,
        active=True,
    )
    session.add(sensor)
    session.flush()

    for step in range(6):
        time = START + timedelta(minutes=30 * step)
        uplink = Uplink(
            time=time, received_at=time, source="own", device_id="node-00"
        )
        session.add(uplink)
        session.flush()
        session.add(
            Reading(
                time=time,
                uplink_id=uplink.id,
                sensor_id=sensor.id,
                value=20.0 + step,
            )
        )

    session.flush()
    return {"building": building.id, "floor": floor.id, "room": room.id}


def test_summarizes_the_readings_of_a_space(client, auth, world):
    response = client.get(f"/spaces/{world['room']}/readings", headers=auth)

    assert response.status_code == 200
    summary = response.json()
    assert len(summary) == 1
    assert summary[0] == {
        "name": "temperature",
        "unit": "Cel",
        "avg": 22.5,
        "min": 20.0,
        "max": 25.0,
        "count": 6,
    }


def test_a_parent_has_no_readings_of_its_own(client, auth, world):
    response = client.get(f"/spaces/{world['building']}/readings", headers=auth)

    assert response.status_code == 200
    assert response.json() == []


def test_descendants_are_included_on_request(client, auth, world):
    response = client.get(
        f"/spaces/{world['building']}/readings",
        params={"include_descendants": True},
        headers=auth,
    )

    assert response.status_code == 200
    assert response.json()[0]["count"] == 6


def test_groups_the_readings_by_hour(client, auth, world):
    response = client.get(
        f"/spaces/{world['room']}/readings", params={"bucket": "hour"}, headers=auth
    )

    assert response.status_code == 200
    buckets = response.json()
    assert len(buckets) == 3
    assert buckets[0]["count"] == 2
    assert buckets[0]["avg"] == 20.5


def test_filters_by_date_range(client, auth, world):
    response = client.get(
        f"/spaces/{world['room']}/readings",
        params={"from": START.isoformat(), "to": (START + timedelta(hours=1)).isoformat()},
        headers=auth,
    )

    assert response.json()[0]["count"] == 2


def test_rejects_an_unsupported_bucket(client, auth, world):
    response = client.get(
        f"/spaces/{world['room']}/readings", params={"bucket": "decade"}, headers=auth
    )

    assert response.status_code == 422


def test_rejects_an_inverted_range(client, auth, world):
    response = client.get(
        f"/spaces/{world['room']}/readings",
        params={"from": START.isoformat(), "to": (START - timedelta(hours=1)).isoformat()},
        headers=auth,
    )

    assert response.status_code == 422


def test_rejects_an_unknown_space(client, auth, world):
    assert client.get("/spaces/9999/readings", headers=auth).status_code == 404

def test_lists_the_devices_of_a_space(client, auth, world):
    response = client.get(f"/spaces/{world['room']}/devices", headers=auth)

    assert response.status_code == 200
    assert [d["device_id"] for d in response.json()] == ["node-00"]


def test_a_parent_has_no_devices_of_its_own(client, auth, world):
    response = client.get(f"/spaces/{world['building']}/devices", headers=auth)

    assert response.json() == []


def test_descendant_devices_are_included_on_request(client, auth, world):
    response = client.get(
        f"/spaces/{world['building']}/devices",
        params={"include_descendants": True},
        headers=auth,
    )

    assert len(response.json()) == 1

def test_renames_a_space(client, admin_auth, world):
    response = client.patch(
        f"/spaces/{world['room']}", json={"name": "Menjador"}, headers=admin_auth
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Menjador"


def test_moves_a_space_to_another_parent(client, admin_auth, world):
    response = client.patch(
        f"/spaces/{world['room']}",
        json={"parent_id": world["building"]},
        headers=admin_auth,
    )

    assert response.json()["parent_id"] == world["building"]


def test_detaches_a_space_from_its_parent(client, admin_auth, world):
    response = client.patch(
        f"/spaces/{world['room']}", json={"parent_id": None}, headers=admin_auth
    )

    assert response.json()["parent_id"] is None


def test_rejects_a_space_as_its_own_parent(client, admin_auth, world):
    response = client.patch(
        f"/spaces/{world['room']}",
        json={"parent_id": world["room"]},
        headers=admin_auth,
    )

    assert response.status_code == 422


def test_rejects_a_cycle(client, admin_auth, world):
    """Moure l'edifici dins del saló deixaria els dos fora de l'arbre."""
    response = client.patch(
        f"/spaces/{world['building']}",
        json={"parent_id": world["room"]},
        headers=admin_auth,
    )

    assert response.status_code == 422


def test_an_omitted_field_is_not_changed(client, admin_auth, world):
    response = client.patch(
        f"/spaces/{world['room']}", json={"name": "Menjador"}, headers=admin_auth
    )

    assert response.json()["parent_id"] == world["floor"]

def test_rejects_an_indirect_cycle(client, admin_auth, world):
    """Moure la planta dins del saló: el cicle no és amb el pare directe, sinó amb un net."""
    response = client.patch(
        f"/spaces/{world['floor']}",
        json={"parent_id": world["room"]},
        headers=admin_auth,
    )

    assert response.status_code == 422

def test_allows_moving_a_space_under_an_unrelated_one(client, admin_auth, session, world):
    """Un espai que no és descendent sí que pot ser el nou pare."""
    other = Space(name="Garatge", type="space", parent_id=world["building"])
    session.add(other)
    session.flush()

    response = client.patch(
        f"/spaces/{world['room']}", json={"parent_id": other.id}, headers=admin_auth
    )

    assert response.status_code == 200