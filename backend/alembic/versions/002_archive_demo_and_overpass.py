"""archive demo leads and add overpass source

Revision ID: 002_archive_demo_and_overpass
Revises: 001_initial_schema
Create Date: 2026-10-16 12:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_archive_demo_and_overpass'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to branches
    with op.batch_alter_table('branches', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        batch_op.add_column(sa.Column('archive_reason', sa.String(length=255), nullable=True))
        batch_op.create_index('ix_branches_is_archived', ['is_archived'])

    # Update demo branches with standard boolean literals compatible with both SQLite and PostgreSQL
    op.execute(
        "UPDATE branches SET is_archived = true, is_demo = true, is_active = false, "
        "archive_reason = 'Quarantined legacy demo fixture' "
        "WHERE is_demo = true OR source_reference LIKE 'DEMO-%'"
    )


def downgrade() -> None:
    with op.batch_alter_table('branches', schema=None) as batch_op:
        batch_op.drop_index('ix_branches_is_archived')
        batch_op.drop_column('archive_reason')
        batch_op.drop_column('is_archived')

