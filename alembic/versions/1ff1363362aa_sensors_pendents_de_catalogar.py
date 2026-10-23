"""sensors pendents de catalogar

Revision ID: 1ff1363362aa
Revises: a4ce28adc9cf
Create Date: 2026-10-23 18:25:10.502653

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1ff1363362aa'
down_revision: Union[str, Sequence[str], None] = 'a4ce28adc9cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "sensors", "sensor_type_id", existing_type=sa.Integer(), nullable=True
    )
    op.create_index(
        "uq_sensors_pending_name",
        "sensors",
        ["source", "device_id", "name"],
        unique=True,
        postgresql_where=sa.text("sensor_type_id IS NULL"),
    )

    # Cada lectura òrfena necessita un sensor pendent al qual apuntar.
    # El NULL va castat: Postgres no en dedueix el tipus dins d'un INSERT SELECT.
    op.execute(
        """
        INSERT INTO sensors (source, device_id, name, active, sensor_type_id)
        SELECT DISTINCT u.source, u.device_id, r.raw_sensor_name, true, NULL::integer
        FROM readings r
        JOIN uplinks u ON r.uplink_id = u.id
        WHERE r.sensor_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE readings r SET sensor_id = s.id
        FROM uplinks u, sensors s
        WHERE r.uplink_id = u.id
          AND r.sensor_id IS NULL
          AND s.source = u.source
          AND s.device_id = u.device_id
          AND s.name = r.raw_sensor_name
          AND s.sensor_type_id IS NULL
        """
    )

    op.drop_index("ix_readings_raw_sensor_name", table_name="readings")
    op.drop_column("readings", "raw_sensor_name")
    op.alter_column(
        "readings", "sensor_id", existing_type=sa.Integer(), nullable=False
    )


def downgrade() -> None:
    op.add_column(
        "readings", sa.Column("raw_sensor_name", sa.String(length=64), nullable=True)
    )
    op.create_index("ix_readings_raw_sensor_name", "readings", ["raw_sensor_name"])
    op.alter_column(
        "readings", "sensor_id", existing_type=sa.Integer(), nullable=True
    )

    op.execute(
        """
        UPDATE readings r
        SET raw_sensor_name = s.name, sensor_id = NULL
        FROM sensors s
        WHERE r.sensor_id = s.id AND s.sensor_type_id IS NULL
        """
    )
    op.execute("DELETE FROM sensors WHERE sensor_type_id IS NULL")

    op.drop_index("uq_sensors_pending_name", table_name="sensors")
    op.alter_column(
        "sensors", "sensor_type_id", existing_type=sa.Integer(), nullable=False
    )