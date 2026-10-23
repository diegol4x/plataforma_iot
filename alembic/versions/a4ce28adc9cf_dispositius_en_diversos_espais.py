"""dispositius en diversos espais

Revision ID: a4ce28adc9cf
Revises: 02832af640d9
Create Date: 2026-10-23 17:43:51.804010

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4ce28adc9cf'
down_revision: Union[str, Sequence[str], None] = '02832af640d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "device_space",
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("device_id", sa.String(length=64), nullable=False),
        sa.Column("space_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source", "device_id"],
            ["devices.source", "devices.device_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["space_id"], ["spaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("source", "device_id", "space_id"),
    )

    # La ubicació passa de columna a taula intermèdia.
    op.execute(
        "INSERT INTO device_space (source, device_id, space_id) "
        "SELECT source, device_id, space_id FROM devices WHERE space_id IS NOT NULL"
    )

    op.drop_constraint(op.f("devices_space_id_fkey"), "devices", type_="foreignkey")
    op.drop_column("devices", "space_id")


def downgrade() -> None:
    op.add_column(
        "devices", sa.Column("space_id", sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.create_foreign_key(
        op.f("devices_space_id_fkey"), "devices", "spaces", ["space_id"], ["id"],
        ondelete="SET NULL",
    )

    # Tornant arrere sols cap una ubicació: es conserva l'espai de menor id.
    op.execute(
        "UPDATE devices d SET space_id = ("
        "  SELECT MIN(ds.space_id) FROM device_space ds "
        "  WHERE ds.source = d.source AND ds.device_id = d.device_id"
        ")"
    )

    op.drop_table("device_space")