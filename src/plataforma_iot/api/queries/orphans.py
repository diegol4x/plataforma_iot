"""Catalogació de sensors pendents quan es dona d'alta la seua magnitud."""

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from plataforma_iot.models.catalog import SensorType
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.telemetry import Reading


def catalogue_pending_sensors(session: Session, sensor_type: SensorType) -> int:
    """Assigna el tipus als sensors que l'esperaven i neteja les seues lectures.

    Torna quants sensors s'han catalogat.
    """
    pending = session.scalars(
        select(Sensor).where(
            Sensor.sensor_type_id.is_(None),
            Sensor.name == sensor_type.code,
        )
    ).all()

    if not pending:
        return 0

    expected_unit = sensor_type.unit.symbol

    for sensor in pending:
        sensor.sensor_type_id = sensor_type.id

    sensor_ids = [sensor.id for sensor in pending]

    # Les que van arribar amb la unitat del tipus deixen de ser sospitoses.
    session.execute(
        update(Reading)
        .where(
            Reading.sensor_id.in_(sensor_ids),
            Reading.received_unit == expected_unit,
        )
        .values(received_unit=None, invalid_message=None)
    )

    # Les que no, canvien de motiu: ja no és "magnitud no catalogada" sinó
    # "unitat discrepant". El missatge es construïx en SQL per a poder incloure
    # la unitat real de cada lectura.
    session.execute(
        update(Reading)
        .where(
            Reading.sensor_id.in_(sensor_ids),
            Reading.received_unit != expected_unit,
        )
        .values(
            invalid_message=func.concat(
                "Unitat rebuda (",
                Reading.received_unit,
                ") distinta de la del tipus ('",
                expected_unit,
                "')",
            )
        )
    )

    return len(pending)