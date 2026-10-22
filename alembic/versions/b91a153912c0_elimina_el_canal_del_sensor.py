"""elimina el canal del sensor

Revision ID: b91a153912c0
Revises: cefec2740bec
Create Date: 2026-10-23 01:13:53.920428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b91a153912c0'
down_revision: Union[str, Sequence[str], None] = 'cefec2740bec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("sensors", "channel")


def downgrade() -> None:
    op.add_column("sensors", sa.Column("channel", sa.Integer(), nullable=True))