"""type de l espai com a enum de bot zone

Revision ID: 818f42d195e2
Revises: 54d468747837
Create Date: 2026-10-23 00:08:06.865999

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '818f42d195e2'
down_revision: Union[str, Sequence[str], None] = '54d468747837'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
