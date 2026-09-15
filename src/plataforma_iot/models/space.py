"""Descripció de la classe"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plataforma_iot.models.base import Base

class Space(Base):
    """Ubicació física o lògica: edifici, sala, planta, ..."""

    __tablename__ = "spaces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("spaces.id",ondelete="RESTRICT"), nullable=True
    )

    parent: Mapped["Space | None"] = relationship(remote_side=[id])

    def __repr__(self) -> str:
        return f"Space(name={self.name!r}, type={self.type!r})"