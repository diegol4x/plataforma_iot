"""Proves de la persistència d'uplinks canònics."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from plataforma_iot.domain.canonical import CanonicalRecord, CanonicalUplink
from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.ingestion.persistence import persist
from plataforma_iot.models.catalog import SensorType, Unit
from plataforma_iot.models.device import Device
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.telemetry import Reading, Uplink

TIME = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def catalogue(session) -> SensorType:
    """Temperatura en graus Celsius, l'única magnitud catalogada."""
    celsius = Unit(name="Grau Celsius", symbol="Cel")
    session.add(celsius)
    session.flush()

    sensor_type = SensorType(code="temperature", name="Temperatura", unit_id=celsius.id)
    session.add(sensor_type)
    session.flush()
    return sensor_type


def _uplink(*records: tuple[str, float, str], received_at: datetime = TIME) -> CanonicalUplink:
    return CanonicalUplink(
        source="own",
        device_id="node-00",
        received_at=received_at,
        records=[
            CanonicalRecord(name=name, value=value, unit=unit, time=TIME)
            for name, value, unit in records
        ],
    )


def _device(session) -> Device:
    return session.get(Device, ("own", "node-00"))


def test_an_unknown_device_is_discovered(session, catalogue):
    """La plataforma accepta les dades però no decidix que el dispositiu és legítim."""
    persist(session, _uplink(("temperature", 21.5, "Cel")))

    device = _device(session)
    assert device is not None
    assert device.status is DeviceStatus.UNPROVISIONED


def test_the_reading_is_stored_with_its_sensor(session, catalogue):
    persist(session, _uplink(("temperature", 21.5, "Cel")))

    reading = session.scalar(select(Reading))
    assert reading.value == 21.5
    assert reading.invalid_message is None
    assert reading.received_unit is None


def test_an_uncatalogued_magnitude_creates_a_pending_sensor(session, catalogue):
    """No es llença una mesura correcta per un error administratiu reversible."""
    persist(session, _uplink(("luminosity", 340.0, "lx")))

    sensor = session.scalar(select(Sensor).where(Sensor.name == "luminosity"))
    assert sensor.sensor_type_id is None

    reading = session.scalar(select(Reading))
    assert reading.received_unit == "lx"
    assert "luminosity" in reading.invalid_message


def test_a_mismatched_unit_is_marked(session, catalogue):
    persist(session, _uplink(("temperature", 294.6, "K")))

    reading = session.scalar(select(Reading))
    assert reading.received_unit == "K"
    assert "Cel" in reading.invalid_message


def test_a_reading_of_an_inactive_sensor_is_marked(session, catalogue):
    persist(session, _uplink(("temperature", 21.5, "Cel")))

    sensor = session.scalar(select(Sensor))
    sensor.active = False
    session.flush()

    persist(session, _uplink(("temperature", 22.0, "Cel"), received_at=TIME + timedelta(minutes=5)))

    readings = session.scalars(select(Reading).order_by(Reading.value)).all()
    assert readings[0].invalid_message is None
    assert readings[1].invalid_message == "Sensor desactivat"


def test_the_sensor_is_reused_between_uplinks(session, catalogue):
    persist(session, _uplink(("temperature", 21.5, "Cel")))
    persist(session, _uplink(("temperature", 22.0, "Cel"), received_at=TIME + timedelta(minutes=5)))

    assert len(session.scalars(select(Sensor)).all()) == 1


def test_a_silent_device_comes_back(session, catalogue):
    persist(session, _uplink(("temperature", 21.5, "Cel")))

    device = _device(session)
    device.status = DeviceStatus.SILENT
    session.flush()

    persist(session, _uplink(("temperature", 22.0, "Cel"), received_at=TIME + timedelta(minutes=5)))

    assert _device(session).status is DeviceStatus.ACTIVE


def test_a_retired_device_does_not(session, catalogue):
    """La retirada és una decisió humana: un uplink no la revoca."""
    persist(session, _uplink(("temperature", 21.5, "Cel")))

    device = _device(session)
    device.status = DeviceStatus.RETIRED
    session.flush()

    persist(session, _uplink(("temperature", 22.0, "Cel"), received_at=TIME + timedelta(minutes=5)))

    assert _device(session).status is DeviceStatus.RETIRED


def test_an_unprovisioned_device_is_not_provisioned_by_data(session, catalogue):
    """Rebre dades no provisiona: eixa és la part asimètrica del descobriment."""
    persist(session, _uplink(("temperature", 21.5, "Cel")))
    persist(session, _uplink(("temperature", 22.0, "Cel"), received_at=TIME + timedelta(minutes=5)))

    assert _device(session).status is DeviceStatus.UNPROVISIONED


def test_last_seen_is_the_reception_time(session, catalogue):
    """El temps de la DADA i el de RECEPCIÓ són coses distintes."""
    received = TIME + timedelta(hours=3)
    persist(session, _uplink(("temperature", 21.5, "Cel"), received_at=received))

    assert _device(session).last_seen == received


def test_the_uplink_time_is_the_earliest_record(session, catalogue):
    uplink = CanonicalUplink(
        source="own",
        device_id="node-00",
        received_at=TIME,
        records=[
            CanonicalRecord(name="temperature", value=21.5, unit="Cel", time=TIME + timedelta(minutes=5)),
            CanonicalRecord(name="temperature", value=22.0, unit="Cel", time=TIME),
        ],
    )

    persist(session, uplink)

    assert session.scalar(select(Uplink)).time == TIME