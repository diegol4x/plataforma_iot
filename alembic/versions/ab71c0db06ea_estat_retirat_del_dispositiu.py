"""estat retirat del dispositiu

Revision ID: ab71c0db06ea
Revises: 1ff1363362aa
Create Date: 2026-10-24 11:02:06.696106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab71c0db06ea'
down_revision: Union[str, Sequence[str], None] = '1ff1363362aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(op.f("ck_devices_status"), "devices", type_="check")
    op.create_check_constraint(
        op.f("ck_devices_status"),
        "devices",
        "status IN ('unprovisioned', 'active', 'silent', 'retired')",
    )


def downgrade() -> None:
    op.execute("UPDATE devices SET status = 'silent' WHERE status = 'retired'")
    op.drop_constraint(op.f("ck_devices_status"), "devices", type_="check")
    op.create_check_constraint(
        op.f("ck_devices_status"),
        "devices",
        "status IN ('unprovisioned', 'active', 'silent')",
    )
