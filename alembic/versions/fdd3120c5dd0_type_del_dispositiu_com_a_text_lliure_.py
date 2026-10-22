"""type del dispositiu com a text lliure opcional

Revision ID: fdd3120c5dd0
Revises: 6dd298856fb1
Create Date: 2026-10-22 23:51:16.250510

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fdd3120c5dd0'
down_revision: Union[str, Sequence[str], None] = '6dd298856fb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "devices",
        "type",
        existing_type=sa.String(length=16),
        type_=sa.String(length=32),
        nullable=True,
    )
    op.execute("UPDATE devices SET type = NULL")


def downgrade() -> None:
    op.execute("UPDATE devices SET type = 'node' WHERE type IS NULL")
    op.alter_column(
        "devices",
        "type",
        existing_type=sa.String(length=32),
        type_=sa.String(length=16),
        nullable=False,
    )