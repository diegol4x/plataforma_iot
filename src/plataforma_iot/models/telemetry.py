"""Telemetria ingerida per la plataforma: uplinks, lectures i descarts."""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    Text,
    Index,
)

from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plataforma_iot.models.base import Base
from plataforma_iot.models.device import Device
from plataforma_iot.models.sensor import Sensor


class Uplink(Base):
    """Missatge rebut, amb la lectura i les metadades del transport"""

    __tablename__ = "uplinks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["source", "device_id"],
            ["devices.source", "devices.device_id"],
            ondelete="CASCADE",
        ),
    )

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False)

    uplink_metadata: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )

    device: Mapped["Device"] = relationship()

    def __repr__(self) -> str:
        return f"Uplink(device_id={self.device_id!r}, time={self.time!r})"


class Reading(Base):
    """Valor puntual observat per un sensor."""

    __tablename__ = "readings"
    __table_args__ = (
        Index("ix_readings_sensor_time", "sensor_id","time"),
    )

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    uplink_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sensor_id: Mapped[int] = mapped_column(
        ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)
    received_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)

    sensor: Mapped["Sensor"] = relationship()

    def __repr__(self) -> str:
        return f"Reading(sensor_id={self.sensor_id!r}, value={self.value!r}, time={self.time!r})"

class Discard(Base):
    """Missatge que no s'ha pogut ingerir amb el motiu pel qual no ha sigut possible"""

    __tablename__ = "discards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str | None] = mapped_column(String(32),  nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True) 
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"Discard(reason={self.reason!r}, received_at={self.received_at})"