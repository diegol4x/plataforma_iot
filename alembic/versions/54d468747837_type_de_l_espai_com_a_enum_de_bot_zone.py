"""type de l espai com a enum de bot zone

Revision ID: 54d468747837
Revises: fdd3120c5dd0
Create Date: 2026-10-23 00:06:36.791161

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54d468747837'
down_revision: Union[str, Sequence[str], None] = 'fdd3120c5dd0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Els valors antics no pertanyen al vocabulari de BOT.
    op.execute("UPDATE spaces SET type = 'storey' WHERE type = 'floor'")
    op.execute("UPDATE spaces SET type = 'space' WHERE type = 'room'")

    op.alter_column(
        "spaces",
        "type",
        existing_type=sa.String(length=32),
        type_=sa.String(length=16),
        existing_nullable=False,
    )
    op.create_check_constraint(
        op.f("ck_spaces_type"),
        "spaces",
        "type IN ('site', 'building', 'storey', 'space')",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_spaces_type"), "spaces", type_="check")
    op.alter_column(
        "spaces",
        "type",
        existing_type=sa.String(length=16),
        type_=sa.String(length=32),
        existing_nullable=False,
    )