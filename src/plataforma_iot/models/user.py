"""Usuaris de la plataforma"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plataforma_iot.domain.user_role import UserRole
from plataforma_iot.models.base import Base
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from plataforma_iot.models.workgroup import Workgroup

class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            name="user_role",
            native_enum=False,
            length=16,
            values_callable=lambda enum: [member.value for member in enum],
            validate_strings=True,
        ),
        nullable=False,
        default=UserRole.VIEWER,
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    workgroups: Mapped[list["Workgroup"]] = relationship(
        secondary="user_workgroup", back_populates="members"
    )

    def __repr__(self) -> str:
        return f"User(username={self.username!r}, role={self.role!r})"