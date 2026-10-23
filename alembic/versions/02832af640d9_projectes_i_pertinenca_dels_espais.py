"""projectes i pertinenca dels espais

Revision ID: 02832af640d9
Revises: 1a321d984702
Create Date: 2026-10-23 12:49:50.770034

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02832af640d9'
down_revision: Union[str, Sequence[str], None] = '1a321d984702'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("workgroup_id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workgroup_id"], ["workgroups.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workgroup_id", "name", name="uq_projects_workgroup_name"),
    )

    # Els espais existents eren de proves i no tenen cap projecte al qual penjar.
    op.execute("UPDATE devices SET space_id = NULL")
    op.execute("DELETE FROM spaces")

    op.add_column("spaces", sa.Column("project_id", sa.Integer(), nullable=False))
    op.create_foreign_key(
        "fk_spaces_project_id", "spaces", "projects", ["project_id"], ["id"], ondelete="RESTRICT"
    )


def downgrade() -> None:
    op.drop_constraint("fk_spaces_project_id", "spaces", type_="foreignkey")
    op.drop_column("spaces", "project_id")
    op.drop_table("projects")