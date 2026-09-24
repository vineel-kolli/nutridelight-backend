"""enforce one active game config

Revision ID: fa0ded0e96c9
Revises: 56532c751d48
Create Date: 2026-09-24 22:01:11.939889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa0ded0e96c9'
down_revision: Union[str, Sequence[str], None] = '56532c751d48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE UNIQUE INDEX uq_one_active_game_config
        ON game_configs (is_active)
        WHERE is_active = TRUE
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS uq_one_active_game_config
        """
    )