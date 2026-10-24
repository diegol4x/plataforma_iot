"""Persistència dels uplinks passats a canònic"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from plataforma_iot.domain.canonical import CanonicalRecord, CanonicalUplink
from plataforma_iot.domain.device_status import DeviceStatus

from plataforma_iot.models.catalog import SensorType
from plataforma_iot.models.device import Device
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.telemetry import Reading, Uplink


UNCATALOGUED_MAGNITUDE = "Magnitud no catalogada: {name!r}"
UNIT_MISMATCH = "Unitat rebuda ({received!r}) distinta de la del tipus ({expected!r})"
INACTIVE_SENSOR = "Sensor desactivat"


def persist(session: Session, uplink: CanonicalUplink) -> None:
    """Persistix el canonical uplink amb totes les seues mesures."""

    device = _upsert_device(session, uplink)

    time = min(record.time for record in uplink.records)
    db_uplink = Uplink(
        time=time,
        received_at=uplink.received_at,
        source=uplink.source,
        device_id=uplink.device_id,
        uplink_metadata=uplink.uplink_metadata,
    )

    session.add(db_uplink)
    session.flush()

    for record in uplink.records:
        # Una magnitud no catalogada no és motiu per a llençar una mesura
        # correcta: el sensor es crea igualment i queda pendent.
        sensor_type = _resolve_sensor_type(session, record.name)
        sensor = _upsert_sensor(session, uplink, record.name, sensor_type)

        session.add(
            Reading(
                time=record.time,
                uplink_id=db_uplink.id,
                sensor_id=sensor.id,
                value=record.value,
                received_unit=_received_unit(record, sensor_type),
                invalid_message=_invalid_message(record, sensor, sensor_type),
            )
        )

    device.last_seen = uplink.received_at
    session.commit()


def _received_unit(record: CanonicalRecord, sensor_type: SensorType | None) -> str | None:
    """La unitat sols es guarda si no es pot donar per descomptada (INV-07)."""

    if sensor_type is None:
        return record.unit

    return record.unit if record.unit != sensor_type.unit.symbol else None


def _invalid_message(
    record: CanonicalRecord, sensor: Sensor, sensor_type: SensorType | None
) -> str | None:
    """Motiu de sospita de la lectura, o None si no n'hi ha cap."""

    if not sensor.active:
        return INACTIVE_SENSOR

    if sensor_type is None:
        return UNCATALOGUED_MAGNITUDE.format(name=record.name)

    if record.unit != sensor_type.unit.symbol:
        return UNIT_MISMATCH.format(received=record.unit, expected=sensor_type.unit.symbol)

    return None


def _upsert_device(session: Session, uplink: CanonicalUplink) -> Device:
    """Recupera el dispositiu o el dona d'alta com a desprovisionat"""

    device = session.get(Device, (uplink.source, uplink.device_id))
    if device is not None:
        if device.status is DeviceStatus.SILENT:
            device.status = DeviceStatus.ACTIVE
        return device

    device = Device(
        source=uplink.source,
        device_id=uplink.device_id,
        status=DeviceStatus.UNPROVISIONED,
    )

    session.add(device)
    session.flush()
    return device


def _resolve_sensor_type(session: Session, name: str) -> SensorType | None:
    """Busca la magnitud al catàleg; si no està, torna None"""

    return session.scalar(select(SensorType).where(SensorType.code == name))


def _upsert_sensor(
    session: Session,
    uplink: CanonicalUplink,
    name: str,
    sensor_type: SensorType | None,
) -> Sensor:
    """Recupera el sensor o el crea a partir de la lectura rebuda.

    Si la magnitud no està catalogada, el sensor es busca pel nom cru: és
    l'únic identificador que tenim fins que algú la done d'alta.
    """
    query = select(Sensor).where(
        Sensor.source == uplink.source,
        Sensor.device_id == uplink.device_id,
    )

    if sensor_type is None:
        query = query.where(Sensor.name == name, Sensor.sensor_type_id.is_(None))
    else:
        query = query.where(Sensor.sensor_type_id == sensor_type.id)

    sensor = session.scalar(query)

    if sensor is not None:
        return sensor

    sensor = Sensor(
        source=uplink.source,
        device_id=uplink.device_id,
        name=name,
        sensor_type_id=sensor_type.id if sensor_type else None,
        active=True,
    )
    session.add(sensor)
    session.flush()
    return sensor