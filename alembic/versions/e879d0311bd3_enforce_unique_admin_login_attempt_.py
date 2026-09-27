"""enforce unique admin login attempt identity

Revision ID: e879d0311bd3
Revises: f5d6d4fa9a5d
"""

from typing import Sequence, Union

from alembic import op


revision: str = "e879d0311bd3"
down_revision: Union[str, Sequence[str], None] = "f5d6d4fa9a5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_admin_login_attempt_username_ip",
        "admin_login_attempts",
        ["username", "ip_address"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_admin_login_attempt_username_ip",
        "admin_login_attempts",
        type_="unique",
    )