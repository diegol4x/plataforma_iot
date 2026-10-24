"""Consultes d'agregació de lectures"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from plataforma_iot.models.catalog import SensorType, Unit
from plataforma_iot.models.sensor import Sensor
from plataforma_iot.models.telemetry import Reading
from plataforma_iot.models.space import Space, device_space

BUCKETS = ("hour", "day")

def _base_query(space_ids: list[int], start: datetime | None, end: datetime | None):
    """Lectures dels dispositius d'uns espais incloent magnitud i unitats"""
    query = (
        select(Reading)
        .join(Sensor, Reading.sensor_id == Sensor.id)
        .join(
            device_space,
            (Sensor.source == device_space.c.source)
            & (Sensor.device_id == device_space.c.device_id),
        )
        .join(SensorType, Sensor.sensor_type_id == SensorType.id)
        .join(Unit, SensorType.unit_id == Unit.id)
        .where(
            device_space.c.space_id.in_(space_ids),
            Sensor.sensor_type_id.is_not(None),
            Sensor.active.is_(True),
        )
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

def descendant_ids(session: Session, space_id: int) -> list[int]:
    """Consulta l'arbre sencer d'ids"""
    roots = select(Space.id).where(Space.id == space_id).cte("tree", recursive=True)

    children = select(Space.id).join(roots, Space.parent_id == roots.c.id)

    tree = roots.union_all(children)

    return list(session.scalars(select(tree.c.id)))