"""lectures de magnituds no catalogades

Revision ID: 11443a5d25fb
Revises: b91a153912c0
Create Date: 2026-10-23 01:39:38.478681

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11443a5d25fb'
down_revision: Union[str, Sequence[str], None] = 'b91a153912c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("readings", sa.Column("raw_sensor_name", sa.String(length=64), nullable=True))
    op.add_column("readings", sa.Column("invalid_message", sa.Text(), nullable=True))
    op.alter_column("readings", "sensor_id", existing_type=sa.Integer(), nullable=True)
    op.create_index("ix_readings_raw_sensor_name", "readings", ["raw_sensor_name"])


def downgrade() -> None:
    op.drop_index("ix_readings_raw_sensor_name", table_name="readings")
    op.execute("DELETE FROM readings WHERE sensor_id IS NULL")
    op.alter_column("readings", "sensor_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("readings", "invalid_message")
    op.drop_column("readings", "raw_sensor_name")