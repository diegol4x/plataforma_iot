"""restriccio de rols d usuari

Revision ID: 6dd298856fb1
Revises: a5d54c679dfa
Create Date: 2026-10-03 17:26:31.318103

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6dd298856fb1'
down_revision: Union[str, Sequence[str], None] = 'a5d54c679dfa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        op.f("ck_users_role"),
        "users",
        "role IN ('viewer', 'admin')",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_users_role"), "users", type_="check")