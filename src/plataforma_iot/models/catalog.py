"""
Descripció:
"""

from sqlalchemy import ForeignKey, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plataforma_iot.models.base import Base


class Unit(Base):
    """Unitat de mesura en què s'expressa un tipus de sensor."""

    __tablename__ = "units"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)

    def __repr__(self) -> str:
        return f"Unit(symbol={self.symbol!r})"


class SensorType(Base):
    """Magnitud del sensor: temperatura, humitat, pressió, ..."""

    __tablename__ = "sensor_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True) #Nom al registre SenML
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    range_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    range_max: Mapped[float | None] = mapped_column(Float, nullable=True)

    unit_id: Mapped[int] = mapped_column(
        ForeignKey("units.id", ondelete="RESTRICT")
    )

    unit: Mapped["Unit"] = relationship()

    def __repr__(self) -> str:
        return f"SensorType(code={self.code!r})"