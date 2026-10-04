"""Consultes d'agregació de lectures"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from plataforma_iot.models.catalog import SensorType, Unit
from plataforma_iot.models.device import Device
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.telemetry import Reading

BUCKETS = ("hour", "day")

def _base_query(space_ids: list[int], start: datetime | None, end: datetime | None):
    """Lectures dels dispositius d'uns espais incloent magnitud i unitats"""
    query = (
        select(Reading)
        .join(Sensor, Reading.sensor_id == Sensor.id)
        .join(
            Device,
            (Sensor.source == Device.source) & (Sensor.device_id == Device.device_id),
        )
        .join(SensorType, Sensor.sensor_type_id == SensorType.id)
        .join(Unit, SensorType.unit_id == Unit.id)
        .where(Device.space_id.in_(space_ids))
    )

    if start is not None:
        query = query.where(Reading.time >= start)
    if end is not None:
        query = query.where(Reading.time < end)

    return query




def summarize(
    session: Session,
    space_ids: list[int],
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict]:
    """Resum per magnitud: mitjana, mínim, màxim i nombre de lectures"""
    query = _base_query(space_ids, start, end).with_only_columns(
        SensorType.code,
        Unit.symbol,
        func.avg(Reading.value),
        func.min(Reading.value),
        func.max(Reading.value),
        func.count(Reading.id),
    ).group_by(SensorType.code, Unit.symbol).order_by(SensorType.code)

    return [
        {
            "name": code,
            "unit": unit,
            "avg": round(float(avg), 2),
            "min": minimum,
            "max": maximum,
            "count": count,
        }
        for code, unit, avg, minimum, maximum, count in session.execute(query)
    ]


def series(
    session: Session,
    space_ids: list[int],
    bucket: str,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict]:
    """Sèrie temporal per magnitud, agrupada per intervals"""
    if bucket not in BUCKETS:
        raise ValueError(f"Interval no suportat: {bucket!r}")

    truncated = func.date_trunc(bucket, Reading.time).label("bucket")

    query = _base_query(space_ids, start, end).with_only_columns(
        truncated,
        SensorType.code,
        Unit.symbol,
        func.avg(Reading.value),
        func.min(Reading.value),
        func.max(Reading.value),
        func.count(Reading.id),
    ).group_by(truncated, SensorType.code, Unit.symbol).order_by(truncated, SensorType.code)

    return [
        {
            "bucket": moment,
            "name": code,
            "unit": unit,
            "avg": round(float(avg), 2),
            "min": minimum,
            "max": maximum,
            "count": count,
        }
        for moment, code, unit, avg, minimum, maximum, count in session.execute(query)
    ]