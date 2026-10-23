"""Descripció de la classe"""

from sqlalchemy import ForeignKey, String, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plataforma_iot.models.base import Base
from plataforma_iot.domain.space_type import SpaceType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plataforma_iot.models.project import Project

class Space(Base):
    """Ubicació física o lògica: edifici, sala, planta, ..."""

    __tablename__ = "spaces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[SpaceType] = mapped_column(
        SAEnum(
            SpaceType,
            name="space_type",
            native_enum=False,
            length=16,
            values_callable=lambda enum: [member.value for member in enum],
            validate_strings=True,
        ),
        nullable=False,
    )

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("spaces.id",ondelete="RESTRICT"), nullable=True
    )

    parent: Mapped["Space | None"] = relationship(remote_side=[id])

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="spaces")

    def __repr__(self) -> str:
        return f"Space(name={self.name!r}, type={self.type!r})"