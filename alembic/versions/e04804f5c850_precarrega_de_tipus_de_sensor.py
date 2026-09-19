"""precarrega de tipus de sensor

Revision ID: e04804f5c850
Revises: 0c8123b7ae25
Create Date: 2026-09-19 ...

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e04804f5c850'
down_revision: Union[str, Sequence[str], None] = '0c8123b7ae25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SENSOR_TYPES = [
    ("temperature", "Temperatura", -40.0, 85.0, "Cel"),
    ("humidity", "Humitat relativa", 0.0, 100.0, "%RH"),
    ("pressure", "Pressió atmosfèrica", 300.0, 1100.0, "hPa"),
]


def upgrade() -> None:
    conn = op.get_bind()
    for code, name, rmin, rmax, symbol in SENSOR_TYPES:
        conn.execute(
            sa.text(
                "INSERT INTO sensor_types (code, name, range_min, range_max, unit_id) "
                "SELECT :code, :name, :rmin, :rmax, id FROM units WHERE symbol = :symbol"
            ),
            {"code": code, "name": name, "rmin": rmin, "rmax": rmax, "symbol": symbol},
        )


def downgrade() -> None:
    codes = ", ".join(f"'{code}'" for code, *_ in SENSOR_TYPES)
    op.execute(f"DELETE FROM sensor_types WHERE code IN ({codes})")