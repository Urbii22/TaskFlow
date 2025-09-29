"""Add search_vector to tasks

Revision ID: 27e5c3007cd9
Revises: 0f91fef8811c
Create Date: 2025-09-29 09:51:33.716352

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '27e5c3007cd9'
down_revision: Union[str, Sequence[str], None] = '0f91fef8811c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) Añadir columna TSVECTOR
    op.add_column(
        "tasks",
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
    )

    # 2) Backfill de datos existentes
    op.execute(
        """
        UPDATE tasks
        SET search_vector = to_tsvector('pg_catalog.english',
            coalesce(title, '') || ' ' || coalesce(description, '')
        );
        """
    )

    # 3) Índice GIN para acelerar @@
    op.create_index(
        "ix_tasks_search_vector",
        "tasks",
        ["search_vector"],
        postgresql_using="gin",
    )

    # 4) Trigger para mantener sincronizado el TSVECTOR en INSERT/UPDATE
    op.execute(
        """
        CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
        ON tasks FOR EACH ROW EXECUTE PROCEDURE
        tsvector_update_trigger(search_vector, 'pg_catalog.english', title, description);
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Revertir trigger, índice y columna
    op.execute("DROP TRIGGER IF EXISTS tsvectorupdate ON tasks;")
    op.drop_index("ix_tasks_search_vector", table_name="tasks")
    op.drop_column("tasks", "search_vector")
