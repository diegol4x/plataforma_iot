"""identitat del dispositiu als descarts

Revision ID: 7f1cab83561a
Revises: 9505bb89c2ee
Create Date: 2026-09-23 09:34:01.871254

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f1cab83561a'
down_revision: Union[str, Sequence[str], None] = '9505bb89c2ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("discards", sa.Column("source", sa.String(length=32), nullable=True))
    op.add_column("discards", sa.Column("device_id", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("discards", "device_id")
    op.drop_column("discards", "source")
