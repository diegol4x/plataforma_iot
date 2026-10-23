"""FK de lectura cap a uplink

Revision ID: d520ffdfdaa4
Revises: 11443a5d25fb
Create Date: 2026-10-23 11:49:23.301476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd520ffdfdaa4'
down_revision: Union[str, Sequence[str], None] = '11443a5d25fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_uplinks_id", "uplinks", ["id"])
    # Les lectures que apunten a un uplink inexistent no poden quedar-se.
    op.execute(
        "DELETE FROM readings WHERE uplink_id NOT IN (SELECT id FROM uplinks)"
    )
    op.create_foreign_key(
        "fk_readings_uplink_id",
        "readings",
        "uplinks",
        ["uplink_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_readings_uplink_id", "readings", type_="foreignkey")
    op.drop_constraint("uq_uplinks_id", "uplinks", type_="unique")