"""Proves del reenllaç de lectures òrfenes en catalogar una magnitud."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.models.catalog import Unit
from plataforma_iot.models.device import Device
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.telemetry import Reading, Uplink

TIME = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def orphan(session) -> Reading:
    """Una lectura d'una magnitud que encara no està catalogada."""
    session.add(Unit(name="Lux", symbol="lx"))
    session.add(
        Device(source="own", device_id="node-00", status=DeviceStatus.ACTIVE)
    )
    session.flush()

    uplink = Uplink(time=TIME, received_at=TIME, source="own", device_id="node-00")
    session.add(uplink)
    session.flush()

    reading = Reading(
        time=TIME,
        uplink_id=uplink.id,
        sensor_id=None,
        raw_sensor_name="luminosity",
        value=340.0,
        received_unit="lx",
        invalid_message="Magnitud no catalogada: 'luminosity'",
    )
    session.add(reading)
    session.flush()
    return reading


def test_cataloguing_relinks_the_orphan(client, admin_auth, session, orphan):
    response = client.post(
        "/sensor_types",
        json={"code": "luminosity", "name": "Il·luminància", "unit_symbol": "lx"},
        headers=admin_auth,
    )

    assert response.status_code == 201
    session.refresh(orphan)
    assert orphan.sensor_id is not None
    assert orphan.invalid_message is None
    assert orphan.received_unit is None


def test_cataloguing_creates_the_missing_sensor(client, admin_auth, session, orphan):
    client.post(
        "/sensor_types",
        json={"code": "luminosity", "name": "Il·luminància", "unit_symbol": "lx"},
        headers=admin_auth,
    )

    sensor = session.scalar(select(Sensor).where(Sensor.name == "luminosity"))
    assert sensor is not None
    assert (sensor.source, sensor.device_id) == ("own", "node-00")


def test_a_mismatched_unit_stays_marked(client, admin_auth, session, orphan):
    """Si la unitat rebuda no és la del tipus, la lectura seguix marcada."""
    session.add(Unit(name="Candela", symbol="cd"))
    session.flush()

    client.post(
        "/sensor_types",
        json={"code": "luminosity", "name": "Il·luminància", "unit_symbol": "cd"},
        headers=admin_auth,
    )

    session.refresh(orphan)
    assert orphan.sensor_id is not None
    assert orphan.received_unit == "lx"
    assert "cd" in orphan.invalid_message


def test_other_magnitudes_are_not_touched(client, admin_auth, session, orphan):
    client.post(
        "/sensor_types",
        json={"code": "pressure", "name": "Pressió", "unit_symbol": "lx"},
        headers=admin_auth,
    )

    session.refresh(orphan)
    assert orphan.sensor_id is None