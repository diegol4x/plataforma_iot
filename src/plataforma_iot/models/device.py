"""Descripció"""

from datetime import datetime
from typing import TYPE_CHECKING


from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Enum as SAEnum,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.models.base import Base

if TYPE_CHECKING:
    from plataforma_iot.models.sensor import Sensor
    from plataforma_iot.models.space import Space
    from plataforma_iot.models.workgroup import Workgroup


class Device(Base):
    """Dispositiu desplegat que envia telemetria.

    Un dispositiu pot estar en diversos espais: el mateix lloc físic es pot
    representar en projectes distints amb nomenclatures distintes. Dins d'un
    mateix projecte, sols pot estar en un espai.
    """

    __tablename__ = "devices"

    source: Mapped[str] = mapped_column(String(32), primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    type: Mapped[str | None] = mapped_column(String(32), nullable=True)
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
    battery_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    spaces: Mapped[list["Space"]] = relationship(
        secondary="device_space", back_populates="devices"
    )
    sensors: Mapped[list["Sensor"]] = relationship(back_populates="device")
    workgroups: Mapped[list["Workgroup"]] = relationship(
        secondary="device_workgroup", back_populates="devices"
    )

    def __repr__(self) -> str:
        return (
            f"Device(source={self.source!r}, device_id={self.device_id!r},"
            f"status={self.status!r})"
        )