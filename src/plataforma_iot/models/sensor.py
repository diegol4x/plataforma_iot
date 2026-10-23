"""Descripció"""

from sqlalchemy import (
    Boolean,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    text,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from plataforma_iot.models.base import Base
from plataforma_iot.models.catalog import SensorType
from plataforma_iot.models.device import Device


class Sensor(Base):
    """Instrument de medició concret muntat a un dispositiu.

    `sensor_type_id` és nullable: un sensor es crea en rebre la primera lectura,
    encara que la seua magnitud no estiga catalogada. Llavors `name` guarda el
    nom cru rebut i el sensor queda pendent fins que algú done d'alta el tipus.

    Un Device té com a màxim un Sensor per SensorType, i un sol Sensor pendent
    per cada nom cru. Per a suportar dos sensors de la mateixa magnitud caldria
    distingir-los per `name` (temperature-interior, temperature-exterior), no
    per un identificador numèric.
    """

    __tablename__ = "sensors"
    __table_args__ = (
        ForeignKeyConstraint(
            ["source", "device_id"],
            ["devices.source", "devices.device_id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("source", "device_id", "sensor_type_id"),
        # Dos NULL no són iguals en SQL, així que la restricció anterior no
        # impedix dos sensors pendents: cal un índex parcial pel nom cru.
        Index(
            "uq_sensors_pending_name",
            "source",
            "device_id",
            "name",
            unique=True,
            postgresql_where=text("sensor_type_id IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sensor_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("sensor_types.id", ondelete="RESTRICT"), nullable=True
    )

    device: Mapped["Device"] = relationship(back_populates="sensors")
    sensor_type: Mapped["SensorType | None"] = relationship()

    def __repr__(self) -> str:
        return f"Sensor(device_id={self.device_id!r}, name={self.name!r})"