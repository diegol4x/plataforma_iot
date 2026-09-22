"""Descripció"""

from datetime import datetime
from typing import TYPE_CHECKING


from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Enum as SAEnum,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.models.base import Base
from plataforma_iot.models.space import Space

if TYPE_CHECKING:
    from plataforma_iot.models.sensor import Sensor

class Device(Base):
    """Dispositiu desplegat amb funció de node o passarel·la"""

    __tablename__ = "devices"

    source: Mapped[str] = mapped_column(String(32), primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum(
            DeviceStatus,
            name="device_status",
            native_enum=False,
            length=32,
            values_callable=lambda enum: [member.value for member in enum],
            validate_strings=True,
        ),
        nullable=False,
        default=DeviceStatus.UNPROVISIONED,
    )
    battery_level: Mapped[int|None] = mapped_column(Integer, nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    space_id: Mapped[int | None] = mapped_column(
        ForeignKey("spaces.id", ondelete="SET NULL"),nullable=True
    )

    space: Mapped["Space | None"] = relationship()
    sensors: Mapped[list["Sensor"]] = relationship(back_populates="device")

    def __repr__(self) -> str:
        return (
            f"Device(source={self.source!r}, device_id={self.device_id!r},"
            f"status={self.status!r})"
        )