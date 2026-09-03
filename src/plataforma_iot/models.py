"""Models de dades de l'aplicació."""

from datetime import datetime
from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Classe base per a tots els models"""

class Lectura(Base):
    __tablename__ = "lectures"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sensor_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"Lectura(sensor_id={self.sensor_id!r}, valor={self.valor}, timestamp={self.timestamp})"