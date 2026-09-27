"""add unique constraint to admin login attempts

Revision ID: f5d6d4fa9a5d
Revises: fa0ded0e96c9
Create Date: 2026-09-27 17:54:19.295315

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5d6d4fa9a5d'
down_revision: Union[str, Sequence[str], None] = 'fa0ded0e96c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_admin_login_attempt_username_ip",
        "admin_login_attempts",
        ["username", "ip_address"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
