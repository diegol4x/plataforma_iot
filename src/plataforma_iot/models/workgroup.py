"""Grups de treball: unitat de pertinença d'usuaris i dispositius"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, ForeignKeyConstraint, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plataforma_iot.models.base import Base

if TYPE_CHECKING:
    from plataforma_iot.models.device import Device
    from plataforma_iot.models.user import User


user_workgroup = Table(
    "user_workgroup",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "workgroup_id",
        ForeignKey("workgroups.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

device_workgroup = Table(
    "device_workgroup",
    Base.metadata,
    Column("source", String(32), primary_key=True),
    Column("device_id", String(64), primary_key=True),
    Column(
        "workgroup_id",
        ForeignKey("workgroups.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    ForeignKeyConstraint(
        ["source", "device_id"],
        ["devices.source", "devices.device_id"],
        ondelete="CASCADE",
    ),
)

class Workgroup(Base):
    """Grup de treball"""

    __tablename__ = "workgroups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    members: Mapped[list["User"]] = relationship(
        secondary=user_workgroup, back_populates="workgroups"
    )
    devices: Mapped[list["Device"]] = relationship(
        secondary=device_workgroup, back_populates="workgroups"
    )

    def __repr__(self) -> str:
        return f"Workgroup(name={self.name!r})"
