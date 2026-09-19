"""precàrrega mínima d'unitats

Revision ID: 0c8123b7ae25
Revises: ba81d3532675
Create Date: ...

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0c8123b7ae25'
down_revision: Union[str, Sequence[str], None] = 'ba81d3532675'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UNITS = [
    ("celsius", "Cel"),
    ("percent relative humidity", "%RH"),
    ("pascal", "Pa"),
    ("hectopascal", "hPa"),
    ("lux", "lx"),
    ("parts per million", "ppm"),
    ("volt", "V"),
    ("ampere", "A"),
    ("watt", "W"),
    ("metre", "m"),
    ("metre per second", "m/s"),
]


def upgrade() -> None:
    units = sa.table(
        "units",
        sa.column("name", sa.String),
        sa.column("symbol", sa.String),
    )
    op.bulk_insert(units, [{"name": name, "symbol": symbol} for name, symbol in UNITS])


def downgrade() -> None:
    symbols = ", ".join(f"'{symbol}'" for _, symbol in UNITS)
    op.execute(f"DELETE FROM units WHERE symbol IN ({symbols})")