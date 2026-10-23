"""Reenllaç de lectures òrfenes quan es cataloga la seua magnitud."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from plataforma_iot.models.catalog import SensorType
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.telemetry import Reading
from plataforma_iot.ingestion.persistence import UNIT_MISMATCH


def relink_orphan_readings(session: Session, sensor_type: SensorType) -> int:
    """Enllaça les lectures que esperaven esta magnitud i torna quantes eren"""
    orphans = session.scalars(
        select(Reading).where(
            Reading.sensor_id.is_(None),
            Reading.raw_sensor_name == sensor_type.code,
        )
    ).all()

    expected_unit = sensor_type.unit.symbol
    sensors: dict[tuple[str, str], Sensor] = {}
    
    for reading in orphans:
        identity = (reading.uplink.source, reading.uplink.device_id)

        if identity not in sensors:
            sensors[identity] = _get_or_create_sensor(session, identity, sensor_type)

        reading.sensor_id = sensors[identity].id

        if reading.received_unit == expected_unit:
            reading.received_unit = None
            reading.invalid_message = None
        else:
            reading.invalid_message = UNIT_MISMATCH.format(
                received=reading.received_unit, expected=expected_unit
            )

    return len(orphans)

def _get_or_create_sensor(
    session: Session, identity: tuple[str, str], sensor_type: SensorType
) -> Sensor:
    """Recupera el sensor del dispositiu per a esta magnitud, o el crea."""
    source, device_id = identity

    sensor = session.scalar(
        select(Sensor).where(
            Sensor.source == source,
            Sensor.device_id == device_id,
            Sensor.sensor_type_id == sensor_type.id,
        )
    )

    if sensor is not None:
        return sensor

    sensor = Sensor(
        source=source,
        device_id=device_id,
        name=sensor_type.code,
        sensor_type_id=sensor_type.id,
        active=True,
    )
    session.add(sensor)
    session.flush()
    return sensor