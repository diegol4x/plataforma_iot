"""adjacencia entre espais

Revision ID: d9f2ddbebdc0
Revises: ab71c0db06ea
Create Date: 2026-10-29 13:15:33.978812

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9f2ddbebdc0'
down_revision: Union[str, Sequence[str], None] = 'ab71c0db06ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "space_adjacency",
        sa.Column("a_id", sa.Integer(), nullable=False),
        sa.Column("b_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["a_id"], ["spaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["b_id"], ["spaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("a_id", "b_id"),
        sa.CheckConstraint("a_id < b_id", name="ck_space_adjacency_ordered"),
    )
    op.create_index("ix_space_adjacency_b", "space_adjacency", ["b_id"])


def downgrade() -> None:
    op.drop_index("ix_space_adjacency_b", table_name="space_adjacency")
    op.drop_table("space_adjacency")