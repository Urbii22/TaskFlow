"""Add deleted_at for soft delete on boards, tasks, comments

Revision ID: e6a3b1b1f4b1
Revises: 27e5c3007cd9
Create Date: 2025-09-30 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e6a3b1b1f4b1"
down_revision: Union[str, Sequence[str], None] = "27e5c3007cd9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add deleted_at columns."""
    op.add_column("boards", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column("tasks", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column("comments", sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema: drop deleted_at columns."""
    op.drop_column("comments", "deleted_at")
    op.drop_column("tasks", "deleted_at")
    op.drop_column("boards", "deleted_at")
