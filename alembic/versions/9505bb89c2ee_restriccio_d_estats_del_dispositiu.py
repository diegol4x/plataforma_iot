"""restriccio d'estats del dispositiu

Revision ID: 9505bb89c2ee
Revises: 575a0c7f69bf
Create Date: 2026-09-22 17:11:16.209273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9505bb89c2ee'
down_revision: Union[str, Sequence[str], None] = '575a0c7f69bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        op.f("ck_devices_status"),
        "devices",
        "status IN ('unprovisioned', 'active', 'silent')",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_devices_status"), "devices", type_="check")