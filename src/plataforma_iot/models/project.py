"""Projectes: agrupació d'espais dins d'un grup de treball."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plataforma_iot.models.base import Base

if TYPE_CHECKING:
    from plataforma_iot.models.space import Space
    from plataforma_iot.models.user import User
    from plataforma_iot.models.workgroup import Workgroup

class Project(Base):
    """Projecte d'un grup de treball"""

    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("workgroup_id", "name", name="uq_projects_workgroup_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    workgroup_id: Mapped[int] = mapped_column(
        ForeignKey("workgroups.id", ondelete="RESTRICT"), nullable=False
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    workgroup: Mapped["Workgroup"] = relationship()
    owner: Mapped["User"] = relationship()
    spaces: Mapped[list["Space"]] = relationship(back_populates="project")

    def __repr__(self) -> str:
        return f"Project(name={self.name!r}, workgroup_id={self.workgroup_id!r})"