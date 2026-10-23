"""Proves de la catalogació de sensors pendents."""

from datetime import datetime, timezone

import pytest

from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.models.catalog import Unit
from plataforma_iot.models.device import Device
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.telemetry import Reading, Uplink
from sqlalchemy import select

TIME = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def pending(session) -> Sensor:
    """Un sensor d'una magnitud que encara no està catalogada, amb una lectura."""
    session.add(Unit(name="Lux", symbol="lx"))
    session.add(Device(source="own", device_id="node-00", status=DeviceStatus.ACTIVE))
    session.flush()

    sensor = Sensor(
        source="own",
        device_id="node-00",
        name="luminosity",
        sensor_type_id=None,
        active=True,
    )
    session.add(sensor)
    session.flush()

    uplink = Uplink(time=TIME, received_at=TIME, source="own", device_id="node-00")
    session.add(uplink)
    session.flush()

    session.add(
        Reading(
            time=TIME,
            uplink_id=uplink.id,
            sensor_id=sensor.id,
            value=340.0,
            received_unit="lx",
            invalid_message="Magnitud no catalogada: 'luminosity'",
        )
    )
    session.flush()
    return sensor


def _reading(session, sensor: Sensor) -> Reading:
    return session.scalar(
        select(Reading).where(Reading.sensor_id == sensor.id)
    )


def test_cataloguing_assigns_the_type_to_the_sensor(client, admin_auth, session, pending):
    response = client.post(
        "/sensor_types",
        json={"code": "luminosity", "name": "Il·luminància", "unit_symbol": "lx"},
        headers=admin_auth,
    )

    assert response.status_code == 201
    session.refresh(pending)
    assert pending.sensor_type_id is not None


def test_its_readings_stop_being_suspicious(client, admin_auth, session, pending):
    """La unitat rebuda era la del tipus: la lectura deixa d'estar marcada."""
    client.post(
        "/sensor_types",
        json={"code": "luminosity", "name": "Il·luminància", "unit_symbol": "lx"},
        headers=admin_auth,
    )

    reading = _reading(session, pending)
    session.refresh(reading)
    assert reading.invalid_message is None
    assert reading.received_unit is None


def test_a_mismatched_unit_changes_the_reason(client, admin_auth, session, pending):
    """Si la unitat rebuda no és la del tipus, la lectura seguix marcada."""
    session.add(Unit(name="Candela", symbol="cd"))
    session.flush()

    client.post(
        "/sensor_types",
        json={"code": "luminosity", "name": "Il·luminància", "unit_symbol": "cd"},
        headers=admin_auth,
    )

    reading = _reading(session, pending)
    session.refresh(reading)
    assert reading.received_unit == "lx"
    assert "lx" in reading.invalid_message
    assert "cd" in reading.invalid_message


def test_other_magnitudes_are_not_touched(client, admin_auth, session, pending):
    client.post(
        "/sensor_types",
        json={"code": "pressure", "name": "Pressió", "unit_symbol": "lx"},
        headers=admin_auth,
    )

    session.refresh(pending)
    assert pending.sensor_type_id is None