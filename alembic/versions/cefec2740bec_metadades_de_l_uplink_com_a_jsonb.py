"""metadades de l uplink com a jsonb

Revision ID: cefec2740bec
Revises: 818f42d195e2
Create Date: 2026-10-23 00:24:40.153644

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'cefec2740bec'
down_revision: Union[str, Sequence[str], None] = '818f42d195e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "uplinks",
        sa.Column(
            "uplink_metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
    )
    # Les columnes de ràdio passen a dins del sac de metadades. Les dades
    # antigues no es recuperen: eren de proves.
    op.drop_column("uplinks", "gateway_id")
    op.drop_column("uplinks", "rssi")
    op.drop_column("uplinks", "snr")
    op.drop_column("uplinks", "spreading_factor")
    op.drop_column("uplinks", "f_cnt")
    op.drop_column("uplinks", "f_port")


def downgrade() -> None:
    op.add_column("uplinks", sa.Column("f_port", sa.Integer(), nullable=True))
    op.add_column("uplinks", sa.Column("f_cnt", sa.Integer(), nullable=True))
    op.add_column("uplinks", sa.Column("spreading_factor", sa.Integer(), nullable=True))
    op.add_column("uplinks", sa.Column("snr", sa.Float(), nullable=True))
    op.add_column("uplinks", sa.Column("rssi", sa.Integer(), nullable=True))
    op.add_column("uplinks", sa.Column("gateway_id", sa.String(length=64), nullable=True))
    op.drop_column("uplinks", "uplink_metadata")