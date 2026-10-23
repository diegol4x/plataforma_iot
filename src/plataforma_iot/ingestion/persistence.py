"""Persistència dels uplinks passats a canònic"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from plataforma_iot.domain.canonical import CanonicalUplink
from plataforma_iot.domain.device_status import DeviceStatus

from plataforma_iot.models.catalog import SensorType
from plataforma_iot.models.device import Device
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.telemetry import Reading, Uplink


UNCATALOGUED_MAGNITUDE = "Magnitud no catalogada: {name!r}"
UNIT_MISMATCH = "Unitat rebuda ({received!r}) distinta de la del tipus ({expected!r})"


def persist(session: Session, uplink: CanonicalUplink) -> None:
    """Persistix el canonical uplink amb totes les seues mesures."""

    device = _upsert_device(session, uplink)

    time = min(record.time for record in uplink.records)
    db_uplink = Uplink(
        time = time,
        received_at = uplink.received_at,
        source = uplink.source,
        device_id = uplink.device_id,
        uplink_metadata = uplink.uplink_metadata,
    )

    session.add(db_uplink)
    session.flush()

    for record in uplink.records:
        sensor_type = _resolve_sensor_type(session, record.name)

        if sensor_type is None:
            # No es llença una mesura correcta per un error administratiu
            # reversible: es guarda orfe i s'enllaçarà en catalogar la magnitud.
            session.add(
                Reading(
                    time=record.time,
                    uplink_id=db_uplink.id,
                    sensor_id=None,
                    raw_sensor_name=record.name,
                    value=record.value,
                    received_unit=record.unit,
                    invalid_message=UNCATALOGUED_MAGNITUDE.format(name=record.name),
                )
            )
            continue

        sensor = _upsert_sensor(session, uplink, record.name, sensor_type)
        expected_unit = sensor_type.unit.symbol
        mismatch = record.unit != expected_unit

        session.add(
            Reading(
                time=record.time,
                uplink_id=db_uplink.id,
                sensor_id=sensor.id,
                value=record.value,
                received_unit=record.unit if mismatch else None,
                invalid_message=(
                    UNIT_MISMATCH.format(received=record.unit, expected=expected_unit)
                    if mismatch
                    else None
                ),
            )
        )
    device.last_seen = uplink.received_at
    session.commit()

def _upsert_device(session: Session, uplink: CanonicalUplink) -> Device:
    """Recupera el dispositiu o el dona d'alta com a desprovisionat"""

    device = session.get(Device, (uplink.source, uplink.device_id))
    if device is not None:
        if device.status is DeviceStatus.SILENT:
            device.status = DeviceStatus.ACTIVE
        return device

    device = Device(
        source= uplink.source,
        device_id=uplink.device_id,
        status=DeviceStatus.UNPROVISIONED,
    )

    session.add(device)
    session.flush()
    return device

def _resolve_sensor_type(session: Session, name: str) -> SensorType | None:
    """Busca la magnitud al catàleg; si no està, torna None"""

    return session.scalar(select(SensorType).where(SensorType.code == name))


def _upsert_sensor(session: Session, uplink: CanonicalUplink, name: str, sensor_type: SensorType,) -> Sensor:
    """Recupera el sensor o el crea a partir de la lectura rebuda."""

    sensor = session.scalar(
        select(Sensor).where(
            Sensor.source == uplink.source,
            Sensor.device_id == uplink.device_id,
            Sensor.sensor_type_id == sensor_type.id,
            )
        )

    if sensor is not None:
        return sensor

    sensor = Sensor(
        source=uplink.source,
        device_id=uplink.device_id,
        name=name,
        sensor_type_id=sensor_type.id,
        active=True,
    )
    session.add(sensor)
    session.flush()
    return sensor