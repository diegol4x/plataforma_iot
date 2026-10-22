"""Descripció"""

from sqlalchemy import (
    Boolean,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from plataforma_iot.models.base import Base
from plataforma_iot.models.catalog import SensorType
from plataforma_iot.models.device import Device

class Sensor(Base):
    """Instrument de medició concret muntat a un dispositiu.
    
    Un Device té com a màxim un Sensor per sensorType. 
    Per a suportar-ne més, caldria distingir-los per `name`
    (temperature-interior, temperature-exterior), no per un identificador numèric.
    """

    __tablename__ = "sensors"
    __table_args__ = (
        ForeignKeyConstraint(
            ["source", "device_id"],
            ["devices.source", "devices.device_id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("source", "device_id", "sensor_type_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sensor_type_id: Mapped[int] = mapped_column(
        ForeignKey("sensor_types.id", ondelete="RESTRICT"), nullable=False
    )

    device: Mapped["Device"] = relationship(back_populates="sensors")
    sensor_type: Mapped["SensorType"] = relationship()

    def __repr__(self) -> str:
        return f"Sensor(device_id={self.device_id!r}, name={self.name!r})"